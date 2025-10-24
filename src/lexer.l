%option noyywrap nodefault yylineno
%x CCOMMENT
%{
  #include <stdio.h>
  #include <string.h>
  #include <stdlib.h>
  #include "parser.tab.h"

  static char* dup_text(void) { return strdup(yytext); }
%}

/* Macros */
WS      [ \t\r]+
ID      [A-Za-z_][A-Za-z0-9_]*
DIGITS  [0-9]+
FLOAT   {DIGITS}"."{DIGITS}
STRING  \"([^\\\n\"]|\\.)*\"

%%

{WS}                          ;
"//".*                        ;
"#".*                         ;

/* Comentário em bloco com start condition */
"/*"                          { BEGIN(CCOMMENT); }
<CCOMMENT>"*/"                { BEGIN(INITIAL); }
<CCOMMENT>\n                  ;   /* mantém contagem de linhas */
<CCOMMENT>.                   ;   /* consome qualquer char */

/* Palavras-chave */
"esteira"                     { return ESTEIRA; }
"var"                         { return VAR; }
"se"                          { return SE; }
"senao"                       { return SENAO; }
"enquanto"                    { return ENQUANTO; }
"ligar"                       { return LIGAR; }
"desligar"                    { return DESLIGAR; }
"iniciar"                     { return INICIAR; }
"parar"                       { return PARAR; }
"definir"                     { return DEFINIR; }
"mostrar"                     { return MOSTRAR; }
"bip"                         { return BIP; }
"esperar"                     { return ESPERAR; }
"sensor"                      { return SENSOR; }
"reg"                         { return REG; }
"mem"                         { return MEM; }

/* Booleanos */
"true"                        { return TRUE; }
"false"                       { return FALSE; }

/* Tipos */
"int"                         { return TYPE_INT; }
"float"                       { return TYPE_FLOAT; }
"bool"                        { return TYPE_BOOL; }
"string"                      { return TYPE_STRING; }

/* Unidades (reservadas) */
"km/h"                        { return UNIT_KM_H; }
"m/s"                         { return UNIT_M_S; }
"%"                           { return UNIT_PERCENT; }
"graus"                       { return UNIT_GRAUS; }
"bpm"                         { return UNIT_BPM; }
"km"                          { return UNIT_KM; }
"min"                         { return UNIT_MIN; }
"ms"                          { return UNIT_MS; }
"m"                           { return UNIT_M; }
"s"                           { return UNIT_S; }

/* Registradores */
"R0"                          { return R0; }
"R1"                          { return R1; }
"R2"                          { return R2; }
"R3"                          { return R3; }

/* Operadores/comparadores (palavra e símbolo) */
"||"                          { return LOR; }
"ou"                          { return LOR; }
"&&"                          { return LAND; }
"e"                           { return LAND; }
"=="                          { return EQEQ; }
"!="                          { return NEQ; }
"<="                          { return LEQ; }
">="                          { return GEQ; }

/* Símbolos de um caractere */
"="                           { return '='; }
"<"                           { return '<'; }
">"                           { return '>'; }
"+"                           { return '+'; }
"-"                           { return '-'; }
"*"                           { return '*'; }
"/"                           { return '/'; }
"%"                           { return '%'; }
"!"                           { return '!'; }
"."                           { return '.'; }
","                           { return ','; }
";"                           { return ';'; }
":"                           { return ':'; }
"("                           { return '('; }
")"                           { return ')'; }
"{"                           { return '{'; }
"}"                           { return '}'; }
"["                           { return '['; }
"]"                           { return ']'; }

/* Literais: FLOAT antes de INT */
{FLOAT}                       { yylval.fval = strtod(yytext, NULL); return FLOAT_LIT; }
{DIGITS}                      { yylval.ival = strtoll(yytext, NULL, 10); return INT_LIT; }
{STRING}                      { yylval.sval = dup_text(); return STRING_LIT; }

/* Identificadores */
{ID}                          { yylval.sval = dup_text(); return IDENT; }

/* Qualquer coisa não reconhecida */
.                             { fprintf(stderr, "[linha %d] caractere inválido: %s\n", yylineno, yytext); return yytext[0]; }

%%

int yywrap(void){ return 1; }
