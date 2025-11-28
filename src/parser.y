%{
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>

  int yylex(void);
  void yyerror(const char* s);

  extern FILE* out; /* definido em driver.c */

  static int label_counter = 0;
  static int new_label(void) { return label_counter++; }

  #define MAX_LOOP_NESTING 128
  static int loop_start_stack[MAX_LOOP_NESTING];
  static int loop_end_stack[MAX_LOOP_NESTING];
  static int loop_top = -1;

  #define MAX_IF_NESTING 128
  static int if_else_stack[MAX_IF_NESTING];
  static int if_end_stack[MAX_IF_NESTING];
  static int if_top = -1;
%}

%define parse.error verbose

%union {
  long long ival;
  double    fval;
  char*     sval;
}

/* tokens vindos do lexer.l */
%token ESTEIRA VAR SE SENAO ENQUANTO LIGAR DESLIGAR INICIAR PARAR DEFINIR MOSTRAR BIP ESPERAR SENSOR REG MEM TRUE FALSE
%token TYPE_INT TYPE_FLOAT TYPE_BOOL TYPE_STRING
%token LOR LAND EQEQ NEQ LEQ GEQ
%token UNIT_KM_H UNIT_M_S UNIT_PERCENT UNIT_GRAUS UNIT_BPM UNIT_KM UNIT_MIN UNIT_MS UNIT_M UNIT_S
%token R0 R1 R2 R3

%token <sval> STRING_LIT IDENT
%token <ival> INT_LIT
%token <fval> FLOAT_LIT

/* Precedência (esqueleto) */
%left LOR
%left LAND
%left EQEQ NEQ
%left '<' '>' LEQ GEQ
%left '+' '-'
%left '*' '/'
%right '!' UMINUS UPLUS

%type <ival> time_val

%%

program
  : ESTEIRA STRING_LIT '{' decls_stmts '}' 
    {
      fprintf(out, "; Programa %s\n", $2);
    }
  ;

decls_stmts
  : /* vazio */
  | decls_stmts decl_or_stmt
  ;

decl_or_stmt
  : var_decl
  | stmt
  ;

/* var: mapeamos tempo/potencia para TIME/POWER da VM */
var_decl
  : VAR IDENT ':' TYPE_INT '=' INT_LIT ';'
    {
      if (strcmp($2, "tempo") == 0) {
        fprintf(out, "SET TIME %lld\n", $6);
      } else if (strcmp($2, "potencia") == 0) {
        fprintf(out, "SET POWER %lld\n", $6);
      } else {
        fprintf(out, "; var %s:int = %lld (nao mapeada na VM)\n", $2, $6);
      }
    }
  | VAR IDENT ':' TYPE_INT ';'
    {
      if (strcmp($2, "tempo") == 0) {
        fprintf(out, "SET TIME 0\n");
      } else if (strcmp($2, "potencia") == 0) {
        fprintf(out, "SET POWER 0\n");
      } else {
        fprintf(out, "; var %s:int; (nao mapeada na VM)\n", $2);
      }
    }
  | VAR IDENT ':' TYPE_FLOAT ';'
    {
      fprintf(out, "; var %s:float; ignorado pela VM\n", $2);
    }
  | VAR IDENT ':' TYPE_BOOL ';'
    {
      fprintf(out, "; var %s:bool; ignorado pela VM\n", $2);
    }
  | VAR IDENT ':' TYPE_STRING ';'
    {
      fprintf(out, "; var %s:string; ignorado pela VM\n", $2);
    }
  ;

/* statements */
stmt
  : assign ';'
  | if_stmt
  | while_stmt
  | action_stmt
  | in_out_stmt
  | ESPERAR time_val ';'
    {
      long long ticks = $2;
      fprintf(out, "; esperar %lld unidades de tempo\n", ticks);
      fprintf(out, "SET TIME %lld\n", ticks);
      int lbl_loop = new_label();
      int lbl_end  = new_label();
      fprintf(out, "L%d:\n", lbl_loop);
      fprintf(out, "DECJZ TIME L%d\n", lbl_end);
      fprintf(out, "GOTO L%d\n", lbl_loop);
      fprintf(out, "L%d:\n", lbl_end);
    }
  | bloco
  ;

bloco
  : '{' decls_stmts '}'
  ;

/* atribuições: tratamos alguns padrões pra gerar código */
assign
  : IDENT '=' INT_LIT
    {
      if (strcmp($1, "tempo") == 0) {
        fprintf(out, "SET TIME %lld\n", $3);
      } else if (strcmp($1, "potencia") == 0) {
        fprintf(out, "SET POWER %lld\n", $3);
      } else {
        fprintf(out, "; atribuicao %s = %lld ignorada pela VM\n", $1, $3);
      }
    }
  | IDENT '=' IDENT '-' INT_LIT
    {
      /* suportamos 'tempo = tempo - 1' */
      if (strcmp($1, "tempo") == 0 &&
          strcmp($3, "tempo") == 0 &&
          $5 == 1) {
        int lbl = new_label();
        fprintf(out, "DECJZ TIME L%d\n", lbl);
        fprintf(out, "L%d:\n", lbl);
      } else {
        fprintf(stderr, "[ERRO] so suportamos 'tempo = tempo - 1' nessa versao do backend\n");
        YYABORT;
      }
    }
  | IDENT '=' IDENT '+' INT_LIT
    {
      /* suportamos 'tempo = tempo + 1' */
      if (strcmp($1, "tempo") == 0 &&
          strcmp($3, "tempo") == 0 &&
          $5 == 1) {
        fprintf(out, "INC TIME\n");
      } else {
        fprintf(stderr, "[ERRO] so suportamos 'tempo = tempo + 1' com +1 nessa versao do backend\n");
        YYABORT;
      }
    }
  ;

/* condicao que realmente compilamos pra VM: tempo > 0 / != 0 */
tempo_cond
  : IDENT '>' INT_LIT
    {
      if (strcmp($1, "tempo") != 0 || $3 != 0) {
        fprintf(stderr, "[ERRO] condicao suportada: 'tempo > 0'\n");
        YYABORT;
      }
    }
  | IDENT NEQ INT_LIT
    {
      if (strcmp($1, "tempo") != 0 || $3 != 0) {
        fprintf(stderr, "[ERRO] condicao suportada: 'tempo != 0'\n");
        YYABORT;
      }
    }
  ;

while_stmt
  : ENQUANTO '(' tempo_cond ')'
    {
      int start = new_label();
      int end   = new_label();
      if (loop_top + 1 >= MAX_LOOP_NESTING) {
        fprintf(stderr, "loop stack overflow\n");
        YYABORT;
      }
      loop_top++;
      loop_start_stack[loop_top] = start;
      loop_end_stack[loop_top]   = end;

      fprintf(out, "L%d:\n", start);
      fprintf(out, "DECJZ TIME L%d\n", end);
    }
    bloco
    {
      int start = loop_start_stack[loop_top];
      int end   = loop_end_stack[loop_top];
      loop_top--;

      fprintf(out, "GOTO L%d\n", start);
      fprintf(out, "L%d:\n", end);
    }
  ;

if_stmt
  : SE '(' tempo_cond ')'
    {
      int elseLabel = new_label();
      int endLabel  = new_label();
      if (if_top + 1 >= MAX_IF_NESTING) {
        fprintf(stderr, "if stack overflow\n");
        YYABORT;
      }
      if_top++;
      if_else_stack[if_top] = elseLabel;
      if_end_stack[if_top]  = endLabel;

      fprintf(out, "DECJZ TIME L%d\n", elseLabel);
    }
    bloco
    {
      int elseLabel = if_else_stack[if_top];
      int endLabel  = if_end_stack[if_top];

      fprintf(out, "GOTO L%d\n", endLabel);
      fprintf(out, "L%d:\n", elseLabel);
      fprintf(out, "L%d:\n", endLabel);
      if_top--;
    }
  | SE '(' tempo_cond ')'
    {
      int elseLabel = new_label();
      int endLabel  = new_label();
      if (if_top + 1 >= MAX_IF_NESTING) {
        fprintf(stderr, "if stack overflow\n");
        YYABORT;
      }
      if_top++;
      if_else_stack[if_top] = elseLabel;
      if_end_stack[if_top]  = endLabel;

      fprintf(out, "DECJZ TIME L%d\n", elseLabel);
    }
    bloco SENAO bloco
    {
      int elseLabel = if_else_stack[if_top];
      int endLabel  = if_end_stack[if_top];

      fprintf(out, "GOTO L%d\n", endLabel);
      fprintf(out, "L%d:\n", elseLabel);
      fprintf(out, "L%d:\n", endLabel);
      if_top--;
    }
  ;

action_stmt
  : LIGAR ';'
    {
      fprintf(out, "SET POWER 60\n");
    }
  | DESLIGAR ';'
    {
      fprintf(out, "SET POWER 0\n");
    }
  | INICIAR ';'
    {
      fprintf(out, "; iniciar (sem instrucao especifica na VM)\n");
    }
  | PARAR ';'
    {
      fprintf(out, "HALT\n");
    }
  | DEFINIR IDENT '=' INT_LIT ';'
    {
      fprintf(out, "; definir %s = %lld (sem mapeamento direto na VM)\n", $2, $4);
    }
  ;

in_out_stmt
  : MOSTRAR '(' IDENT ')' ';'
    {
      if (strcmp($3, "tempo") != 0) {
        fprintf(stderr,
                "[ERRO] nesta versao so suportamos mostrar(tempo)\n");
        YYABORT;
      }
      fprintf(out, "PRINT\n");
    }
  | BIP ';'
    {
      fprintf(out, "; bip\n");
    }
  ;

time_val
  : INT_LIT UNIT_MS
    { $$ = $1; }
  | INT_LIT UNIT_S
    { $$ = $1 * 1000; }
  | INT_LIT UNIT_MIN
    { $$ = $1 * 60000; }
  ;

%%

void yyerror(const char* s) {
  extern int yylineno;
  fprintf(stderr, "[linha %d] erro sintatico: %s\n", yylineno, s);
}
