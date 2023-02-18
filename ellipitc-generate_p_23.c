#include<stdio.h>
#include<ctype.h>
#include<string.h>
#include<stdlib.h>
#include<math.h>
#include<time.h>
#include<limits.h>
#include<float.h>
#include<setjmp.h>
#include<signal.h>

#define WORD_BASE 32
#define s 5

int prime_check(int ans) {
    int t = 0;
    
    for (int i=3;i<100; i++) {
        if (ans%i == 0)
            t = 1;
    }
    return t;
}


int prime_gen() {
    
    srand((unsigned int)time(NULL));
    
    int i,ans;
    while(prime_check(ans) == 1){
        ans = 3 + rand()%25;
    }
    
    
    return ans;
}



int plus_unm(int x,int mod){
    if(x<=0)     x=x+mod;
    return x;
}

int reve_num(int x,int mod){
    int ans;
    
    x = plus_unm(x,mod);
    
    for(int i =0; i<mod;i++){
        if((x*i)%mod == 1){
            ans = i;
            break;
        }
    }
    return ans;
}

int point_plus_x(int xP,int yP,int xQ,int yQ,int a,int b,int p){
    int xR,yR,lamd,up,under,under_1,myu;
    if(xP == xQ){
        xR=((xP*xP*xP*xP-2*a*xP*xP-8*b*xP+b*b)%p*reve_num(4*yP*yP,p))%p;
        
        for (int i=0;i<p; i++) {
            if((i*i)%p == (xR*xR*xR +a*xR +b)%p){
                yR = i;
                break;
            }
        }
    }
    else if(xP != xQ){
        up=(yP-yQ)%p;
        up = plus_unm(up,p);
        under_1 =(xP-xQ)%p;
        under = (reve_num(under_1,p))%p;
        lamd = (up*under)%p;
        myu = (yP-xP*lamd)%p;
        xR=(lamd*lamd-xP-xQ-0)%p;
        yR=(lamd*xR+myu)%p;
    }
    return xR;
}


int point_plus_y(int xP,int yP,int xQ,int yQ,int a,int b,int p){
    int xR,yR,lamd,up,under,under_1,myu;
    if(xP == xQ){
        xR=((xP*xP*xP*xP-2*a*xP*xP-8*b*xP+b*b)%p*reve_num(4*yP*yP,p))%p;
        
        for (int i=0;i<p; i++) {
            if((i*i)%p == (xR*xR*xR +a*xR +b)%p){
                yR = i;
                break;
            }
        }
    }
    else if(xP != xQ){
        up=(yP-yQ)%p;
        up = plus_unm(up,p);
        under_1 =(xP-xQ)%p;
        under = (reve_num(under_1,p))%p;
        lamd = (up*under)%p;
        myu = (yP-xP*lamd)%p;
        xR=(lamd*lamd-xP-xQ-0)%p;
        yR=(lamd*xR+myu)%p;
    }
    return yR;
}



int main(){
    int a,b,p=23,ans;
    int xP,yP,xQ,yQ,xR,yR,xS,yS,lamd,up,under,under_1,myu,x,y;
    char str[8];
    
    srand((unsigned int)time(NULL));
    
    printf("ランダムで楕円曲線を作りますか？→YES:0/NO:1\n");
    scanf("%d",&ans);
    if (ans == 0) {
        do {
            a =   rand()%4;
            b =   rand()%4;
        }
        while (4*a*a*a+27*b*b == 0);
    }
    else{
        while(4*a*a*a+27*b*b == 0){
            printf("4a^3+27b^2=0とならないa,bを入力してください\n");
            printf("aを入力してください\n");
            scanf("%d",&a);
            printf("bを入力してください\n");
            scanf("%d",&b);
            
        }
    }
    printf("楕円曲線はy^2=x^3+%dx+%dです\n",a,b);
    /*printf("ランダムで有限体Fpを作りますか？→YES:0/NO:1\n");
    scanf("%d",&ans);
    if (ans == 0) {
        p = prime_gen();
    }
    else
    { */      printf("有限体Fpの素数を23とします\n");
            p = 23;
        
        
    //}
    
    
    printf("FpのPは%dです\n",p);
    printf("y^2=x^3+%dx+%dはF%d上での点は下記の通りです\n",a,b,p);
    
    for(int i =0; i<p;i++){
        for(int j =0; j<p;j++){
            if((i*i*i + a*i +b -j*j )%p == 0){
                printf("(%d,%d) ",i,j);
            }
        }
    }
    printf("\n 足し算をしてみましょう\n");
    printf("1つ目の点のx座標は？\n");
    scanf("%d",&xP);
    printf("1つ目の点のy座標は？\n");
    scanf("%d",&yP);
    printf("2つ目の点のx座標は？\n");
    scanf("%d",&xQ);
    printf("2つ目の点のy座標は？\n");
    scanf("%d",&yQ);
    printf("その足し算は");
    xR = point_plus_x(xP,yP,xQ,yQ,a,b,p);
    yR = point_plus_y(xP,yP,xQ,yQ,a,b,p);
    printf("(%d,%d) \n",xR,yR);
    
    
    
    xS = xP;
    yS = yP;
    
    for (int i = 2; i<22; i++) {
        printf("%dPは",i);
        xR = point_plus_x(xP,yP,xS,yS,a,b,p);
        yR = point_plus_y(xP,yP,xS,yS,a,b,p);
        printf("(%d,%d) \n ",xR,yR);
        xS = xR;
        yS = yR;
        
    }
    
}
    

