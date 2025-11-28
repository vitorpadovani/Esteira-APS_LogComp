#include <stdio.h>
#include <stdlib.h>

#include "parser.tab.h"

FILE* out = NULL;
extern FILE* yyin;
int yyparse(void);

int main(int argc, char** argv) {
    const char* in_name  = NULL;
    const char* out_name = "programa.mwasm";

    if (argc >= 2) {
        in_name = argv[1];       /* fonte na sua linguagem */
    }
    if (argc >= 3) {
        out_name = argv[2];      /* nome do .mwasm de saída */
    }

    if (in_name) {
        yyin = fopen(in_name, "r");
        if (!yyin) {
            perror(in_name);
            return 1;
        }
    }

    out = fopen(out_name, "w");
    if (!out) {
        perror(out_name);
        if (yyin) fclose(yyin);
        return 1;
    }

    fprintf(out, "; Codigo gerado pela linguagem ESTEIRA para MicrowaveVM\n");

    int res = yyparse();
    if (res != 0) {
        fprintf(stderr, "Falha na compilacao\n");
    }

    /* Garante parada, caso o programa fonte nao tenha PARAR; */
    fprintf(out, "HALT\n");

    fclose(out);
    if (yyin) fclose(yyin);
    return res;
}
