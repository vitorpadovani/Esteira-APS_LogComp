%{
  #include <stdio.h>
  #include <stdlib.h>

  int yylex(void);
  void yyerror(const char* s) {
    extern int yylineno;
    fprintf(stderr, "[linha %d] erro sintatico: %s\n", yylineno, s);
  }
%}

%define parse.error verbose

%union {
  long long ival;
  double    fval;
  char*     sval;
}

/* Palavras-chave e símbolos compostos */
%token ESTEIRA VAR SE SENAO ENQUANTO LIGAR DESLIGAR INICIAR PARAR DEFINIR MOSTRAR BIP ESPERAR SENSOR REG MEM TRUE FALSE
%token TYPE_INT TYPE_FLOAT TYPE_BOOL TYPE_STRING
%token LOR LAND EQEQ NEQ LEQ GEQ
%token UNIT_KM_H UNIT_M_S UNIT_PERCENT UNIT_GRAUS UNIT_BPM UNIT_KM UNIT_M UNIT_MIN UNIT_S UNIT_MS
%token R0 R1 R2 R3

/* Literais e ids */
%token <sval> STRING_LIT IDENT
%token <ival> INT_LIT
%token <fval> FLOAT_LIT

/* Precedência */
%left LOR
%left LAND
%left EQEQ NEQ
%left '<' '>' LEQ GEQ
%left '+' '-'
%left '*' '/' '%'
%right UMINUS UPLUS '!'  /* unários */

%%

program
  : ESTEIRA STRING_LIT '{' decls_stmts_opt '}'     { printf("OK\n"); }
  ;

decls_stmts_opt
  : /* vazio */
  | decls_stmts
  ;

decls_stmts
  : decl_or_stmt
  | decls_stmts decl_or_stmt
  ;

decl_or_stmt
  : var_decl
  | stmt
  ;

/* var e lista de ids */
var_decl
  : VAR id_list opt_type opt_init ';'
  ;

id_list
  : IDENT
  | id_list ',' IDENT
  ;

opt_type
  : /* vazio */
  | ':' type
  ;

type
  : TYPE_INT
  | TYPE_FLOAT
  | TYPE_BOOL
  | TYPE_STRING
  ;

opt_init
  : /* vazio */
  | '=' expr
  ;

/* instruções */
stmt
  : assign ';'
  | if_stmt
  | while_stmt
  | action_stmt
  | in_out_stmt
  | ESPERAR time_val ';'
  | bloco
  ;

assign
  : lvalue '=' expr
  ;

lvalue
  : IDENT
  | MEM '[' expr ']'
  ;

bloco
  : '{' decls_stmts_opt '}'
  ;

if_stmt
  : SE '(' expr ')' bloco opt_else
  ;

opt_else
  : /* vazio */
  | SENAO bloco
  ;

while_stmt
  : ENQUANTO '(' expr ')' bloco
  ;

action_stmt
  : LIGAR ';'
  | DESLIGAR ';'
  | INICIAR ';'
  | PARAR ';'
  | DEFINIR alvo '=' dim_val ';'
  ;

alvo
  : IDENT
  ;

in_out_stmt
  : MOSTRAR '(' expr expr_list_opt ')' ';'
  | BIP ';'
  ;

expr_list_opt
  : /* vazio */
  | ',' expr expr_list_opt
  ;

/* unidades */
dim_val
  : expr unit_opt
  ;

unit_opt
  : /* vazio */
  | unit
  ;

unit
  : UNIT_KM_H
  | UNIT_M_S
  | UNIT_PERCENT
  | UNIT_GRAUS
  | UNIT_BPM
  | UNIT_KM
  | UNIT_M
  | UNIT_MIN
  | UNIT_S
  ;

time_val
  : expr UNIT_MS
  | expr UNIT_S
  | expr UNIT_MIN
  ;

/* expressões */
expr
  : or_expr
  ;

or_expr
  : and_expr
  | or_expr LOR and_expr
  ;

and_expr
  : eq_expr
  | and_expr LAND eq_expr
  ;

eq_expr
  : rel_expr
  | eq_expr EQEQ rel_expr
  | eq_expr NEQ  rel_expr
  ;

rel_expr
  : add_expr
  | rel_expr '<'  add_expr
  | rel_expr '>'  add_expr
  | rel_expr LEQ  add_expr
  | rel_expr GEQ  add_expr
  ;

add_expr
  : mul_expr
  | add_expr '+' mul_expr
  | add_expr '-' mul_expr
  ;

mul_expr
  : un_expr
  | mul_expr '*' un_expr
  | mul_expr '/' un_expr
  | mul_expr '%' un_expr
  ;

un_expr
  : '!' un_expr
  | '-' un_expr %prec UMINUS
  | '+' un_expr %prec UPLUS
  | primary
  ;

primary
  : literal
  | IDENT
  | SENSOR '.' IDENT
  | REG '(' reg ')'
  | MEM '[' expr ']'
  | '(' expr ')'
  ;

reg
  : R0
  | R1
  | R2
  | R3
  ;

literal
  : INT_LIT
  | FLOAT_LIT
  | STRING_LIT
  | TRUE
  | FALSE
  ;

%%

int main(int argc, char** argv) {
  if (argc > 1) {
    FILE* f = fopen(argv[1], "r");
    if (!f) { perror("erro ao abrir arquivo"); return 1; }
    extern FILE* yyin;
    yyin = f;
  }
  return yyparse();
}
