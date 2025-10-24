/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

#ifndef YY_YY_PARSER_TAB_H_INCLUDED
# define YY_YY_PARSER_TAB_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    ESTEIRA = 258,                 /* ESTEIRA  */
    VAR = 259,                     /* VAR  */
    SE = 260,                      /* SE  */
    SENAO = 261,                   /* SENAO  */
    ENQUANTO = 262,                /* ENQUANTO  */
    LIGAR = 263,                   /* LIGAR  */
    DESLIGAR = 264,                /* DESLIGAR  */
    INICIAR = 265,                 /* INICIAR  */
    PARAR = 266,                   /* PARAR  */
    DEFINIR = 267,                 /* DEFINIR  */
    MOSTRAR = 268,                 /* MOSTRAR  */
    BIP = 269,                     /* BIP  */
    ESPERAR = 270,                 /* ESPERAR  */
    SENSOR = 271,                  /* SENSOR  */
    REG = 272,                     /* REG  */
    MEM = 273,                     /* MEM  */
    TRUE = 274,                    /* TRUE  */
    FALSE = 275,                   /* FALSE  */
    TYPE_INT = 276,                /* TYPE_INT  */
    TYPE_FLOAT = 277,              /* TYPE_FLOAT  */
    TYPE_BOOL = 278,               /* TYPE_BOOL  */
    TYPE_STRING = 279,             /* TYPE_STRING  */
    LOR = 280,                     /* LOR  */
    LAND = 281,                    /* LAND  */
    EQEQ = 282,                    /* EQEQ  */
    NEQ = 283,                     /* NEQ  */
    LEQ = 284,                     /* LEQ  */
    GEQ = 285,                     /* GEQ  */
    UNIT_KM_H = 286,               /* UNIT_KM_H  */
    UNIT_M_S = 287,                /* UNIT_M_S  */
    UNIT_PERCENT = 288,            /* UNIT_PERCENT  */
    UNIT_GRAUS = 289,              /* UNIT_GRAUS  */
    UNIT_BPM = 290,                /* UNIT_BPM  */
    UNIT_KM = 291,                 /* UNIT_KM  */
    UNIT_M = 292,                  /* UNIT_M  */
    UNIT_MIN = 293,                /* UNIT_MIN  */
    UNIT_S = 294,                  /* UNIT_S  */
    UNIT_MS = 295,                 /* UNIT_MS  */
    R0 = 296,                      /* R0  */
    R1 = 297,                      /* R1  */
    R2 = 298,                      /* R2  */
    R3 = 299,                      /* R3  */
    STRING_LIT = 300,              /* STRING_LIT  */
    IDENT = 301,                   /* IDENT  */
    INT_LIT = 302,                 /* INT_LIT  */
    FLOAT_LIT = 303,               /* FLOAT_LIT  */
    UMINUS = 304,                  /* UMINUS  */
    UPLUS = 305                    /* UPLUS  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 14 "parser.y"

  long long ival;
  double    fval;
  char*     sval;

#line 120 "parser.tab.h"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_PARSER_TAB_H_INCLUDED  */
