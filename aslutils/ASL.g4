grammar ASL;

start
   : statement*
   ;

statement
   : If expression Then block (Elsif expression Then block)* (Else block)?
   | Case expression Of Start (When (literal | Identifier) block)* (Otherwise block)? End
   | Repeat block Until expression Semicolon Newline?
   | While expression Do block
   | For assignableExpr Assign expression (To | Downto) expression block
   | simpleStatement Newline?
   ;

simpleStatement
   : Undefined Semicolon
   | Unpredictable Semicolon
   | See expression Semicolon
   | Implementation_Defined String Semicolon
   | Assert expression Semicolon
   | Enumeration Identifier LeftBrace Identifier (Comma Identifier)* RightBrace Semicolon
   | Constant? typeName assignableExpr (Comma assignableExpr)* Semicolon
   | Constant? typeName? assignableExpr Assign expression Semicolon
   | Identifier LeftParen (expression (Comma expression)*)? RightParen Semicolon
   ;

block
   : Start statement+ End
   | simpleStatement* Newline
   ;

expression
   : If expression Then expression Else expression
   | literal
   | LeftParen expression Comma expression (Comma expression)* RightParen
   | LeftParen expression RightParen
   | Identifier LeftParen (expression (Comma expression)*)? RightParen
   | Identifier LeftBracket (expression (Comma expression)*)? RightBracket
   | expression Dot? LeftBrace expression (RangeDown expression)? (Comma expression (RangeDown expression)?)* RightBrace
   | expression Dot Identifier
   | (Not | Plus | Minus | Negation) expression
   | expression (Mult | Divide | Div | Mod) expression
   | expression (Plus | Minus) expression
   | expression Colon expression
   | expression (RightShift | LeftShift) expression
   | expression (Greater | Less | Equal | NotEqual | GreaterEqual | LessEqual) expression
   | expression (And | Eor | Or | Lor | Land) expression
   | expression In LeftBrace expression (Comma expression)* RightBrace
   | typeName Unknown
   | Identifier
   ;

assignableExpr
   : LeftParen assignableExpr Comma assignableExpr (Comma assignableExpr)* RightParen
   | Identifier LeftBracket (expression (Comma expression)*)? RightBracket
   | assignableExpr Colon assignableExpr
   | assignableExpr Dot? LeftBrace expression (RangeDown expression)? (Comma expression (RangeDown expression)?)* RightBrace
   | assignableExpr Dot? Identifier
   | Identifier
   | Minus
   ;

literal
   : Integer
   | Hex
   | BitVector
   | BitPattern
   | FixedPointNum
   | Bool
   | String
   ;

typeName
   : IntegerType
   | BooleanType
   | BitsType LeftParen expression RightParen
   | BitType
   | RealType
   | Identifier
   ;

If : 'if';
Then : 'then';
Elsif : 'elsif';
Else : 'else';
Case : 'case';
Of : 'of';
When : 'when';
Otherwise : 'otherwise';
For : 'for';
To : 'to';
Downto : 'downto';
While : 'while';
Do : 'do';
Repeat : 'repeat';
Until : 'until';
Return : 'return';
Assert : 'assert';
Consistent : 'Consistent';
Enumeration : 'enumeration';
Constant : 'constant';
Is : 'is';
Array : 'array';
Quot : 'QUOT';
Rem : 'REM';
Div : 'DIV';
Mod : 'MOD';
And : 'AND';
Not : 'NOT';
Or : 'OR';
Eor : 'EOR';
In : 'IN';
Undefined : 'UNDEFINED';
Unknown : 'UNKNOWN';
Unpredictable : 'UNPREDICTABLE';
Constrained_Unpredictable : 'CONSTRAINED_UNPREDICTABLE';
See : 'SEE';
Implementation_Defined : 'IMPLEMENTATION_DEFINED';
Subarchitecture_Defined : 'SUBARCHITECTURE_DEFINED';
Raise : 'RAISE';
Try : 'try';
Catch : 'catch';
Throw : 'throw';
Typeof : 'typeof' | 'TypeOf';
IntegerType : 'integer';
BooleanType : 'boolean';
BitsType : 'bits';
BitType : 'bit';
RealType : 'real';
Start : 'START';
End : 'END';
Newline : 'NEWLINE';

Equal : '==';
NotEqual : '!=';
Greater : '>';
Less : '<';
GreaterEqual : '>=';
LessEqual : '<=';
Lor : '||';
Land : '&&';
Negation : '!';
RangeUp : '+:';
RangeDown : '-:';
Colon : ':';
LeftBracket : '[';
RightBracket : ']';
Mult : '*';
Divide : '/';
Plus : '+';
Minus : '-';
LeftShift : '<<';
RightShift : '>>';
Pow : '^';
Assign : '=';
LeftParen : '(';
RightParen : ')';
LeftBrace : '{';
RightBrace : '}';
Comma : ',';
Dot : '.';
Semicolon : ';';

Bool
   : 'TRUE' | 'FALSE'
   ;

Identifier
   : (('AArch32' | 'AArch64') '.')? [a-zA-Z_] [a-zA-Z0-9_]*
   ;

Integer
   : '0' | [1-9] [0-9]*
   ;

Hex
   : '0x' [0-9A-Fa-f_]+
   ;

FixedPointNum
   : ('0' | [1-9] [0-9]*) [.] [0-9]+
   ;

BitVector
   : '\'' [01 ]+ '\''
   ;

BitPattern
   : '\'' [01 x]+ '\''
   ;

String
   : '"' ~["]* '"'
   ;

Ws
   : [ \t\n\r] + -> skip
   ;

LineComment
   :   '//' ~[\r\n]* -> skip
   ;
