* `1a.yaml` (git commit `03595de8d7fc5375a860f5ba52f787d2be7f05a6`)

    | LM | LM weight | beam | CTC weight | Length Norm | dev93 (SUB/INS/DEL) | eval92 (SUB/INS/DEL) |
    |:---:|:---:|:---:|:---:|:---:|:---:|:---:|
    | - | 0 | 8 | 0 | true | 15.95% (983/170/176) | 13.47% (574/110/84) |
    | - | 0 | 8 | 1 | false | 24.90% (1689/236/150) | 19.61% (896/142/80) |
    | - | 0 | 8 | 0.4 | false | 15.92% (1008/163/156) | 12.46% (548/93/69) |
    | RNN | 0.5 | 8 | 0.4 | false | 11.21% (688/133/113) | 8.32% (341/81/52) |
    | RNN | 0.5 | 16 | 0.4 | false | 10.78% (662/139/97) | 7.81% (319/85/41) |
    | RNN | 0.6 | 16 | 0.4 | false | 10.44% (639/133/98) | 7.37% (300/82/38) |
