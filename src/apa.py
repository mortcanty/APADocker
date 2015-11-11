#!/usr/bin/env python
#  Name:  
#    apa.py
#
#  Purpose:  
#    Perfrom acquisition path analysis
#
#  Usage:        
#        Calculate optimal inspection strategies 
#        from acquisition path analysis
#        
#        python %s [-h] [-d] [-b value] Inspection_effort
#        -h this usage message
#        -d draw diversion path graph
#        -b set perceived sanction parameter
#           (incentive d is 9 for most attractive path)
#
#  Copyright (c) 2015, Mort Canty, Clemens Listner
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

from numpy import * 
from itertools import combinations
from nash.nasheq import nashEquilibria
from AcquisitionNetwork_PM import AcquisitionNetwork 
import sys, time, getopt
import operator
import matplotlib.pyplot as plt

def undominated(K,Ks):
    for KK in Ks:
        if set(K) <= set(KK):
            return False 
    return True

def APA(ps,ls,betas,alphas,ws,W,b=1,f=1,a=10,c=100,e=1,
        select='one',s1=0,verbose=True):  
#        Acquisition path analysis game theoretical effectiveness evaluation
#     Usage:
#      python APA(ps,ls,betas,alphas,ws,W,b=10,f=1,a=10,c=100,e=1) 
#      ps =    list of acquisition paths. Each path consists 
#              of a list of locations/activities
#      ls =    list of corresponding path lengths
#      betas = list of non-detection probabilities in event of  
#             violation and inspection at a location/activity
#      alphas = false alarm probability in event of inspection of 
#               location/activity where State has behaved legally
#      ws =    list of inspection efforts (person-days) for each 
#              activity/location
#      W  =    available inspection effort (person-days)
#      b =     perceived sanction in event of detection relative 
#              to the payoff 10 for undetected violation 
#              along the shortest path.   
#      f =     false alarm resolution cost for any location/activity 
#              on same scale as above
#      k =     number of locations/activities inspected
#      a,c,e = IAEA utilities (-a = loss for detection, 
#              -c = loss for undetected violation, 
#              -e loss incurred by false alarm)
#      s1 = use s1+1 almost complementary path for Lehmke-Howson
#      All utilities are normalized to the utility 0 for 
#      legal behavior (deterrence) for both players     
#      Returns equilibria as a list of tuples [(P*,H1*,Q*,H2*), ...]
#      (c) Mort Canty 2015

    ls = asarray(ls)
    ps = asarray(ps)
    ws = asarray(ws) 
    betas = asarray(betas)
    alphas = asarray(alphas)             
    n = len(ps)
    m = len(betas)
#  pure strategies of Inspectorate    
    Ks = []
    if verbose:
        print 'Enumerating feasible undominated inspection strategies ...'
    idx = argsort(ws)
    cs = cumsum(ws[idx])
#  largest possible number of activities   
    kl = 0
    while kl < len(cs) and cs[kl] <= W:
        kl += 1  
    if verbose:      
        print 'Largest inspection strategy has %i activities'%kl       
    for i in range(kl,0,-1):
        cm = combinations(range(m),i)
        while True:
            try:
                K = list(cm.next())
                if (sum(ws[K]) <= W) and undominated(K,Ks):
                    Ks.append(K)
            except:
                break  
        if verbose:  
            print 'length: %i cumulative inspectorate strategies: %i' \
                                                        %(i,len(Ks))               
    mk = len(Ks)
#  path preferences inversely proportional to path lengths    
    ds = 1./ls
#  path preferences in decreasing order beginning with 10    
    ds = 9*ds/ds[0]
#  construct bimatrix
    print 'Building bimatrix...'
    A = zeros((mk,n+1))
    B = zeros((mk,n+1))
    i = 0
    for K in Ks:
        K = set(K)
        for j in range(n+1):
            if j<n: 
                P = set(ps[j])
            else:
                P = set([])    
            beta = 1
            for ell in K & P:
                beta *= betas[ell]
            tmp = 1
            for ell in K - (K & P):
                tmp *= 1 - alphas[ell]
            alpha = 1 - tmp 
            if j < n:         
                A[i,j] = -c*beta - a*(1-beta) - e*alpha
                B[i,j] = (ds[j])*beta - b*(1-beta) -f*alpha
            else:
                A[i,j] = -e*alpha
                B[i,j] = -f*alpha         
        i += 1
#  solve the game     
    print 'Calling nashEquilibria on %i by %i bimatrix ...'%(mk,n+1)      
    return (Ks,nashEquilibria(A.tolist(),B.tolist(),select=select,s1=s1))

def simulate():
# simulation   
    random.seed(654321)
    start = time.time()   
    edges = 10
    betas = random.rand(edges)*0.5 
    alphas = zeros(edges)+0.05
    ws = random.random(edges)
    W = 2.0
    ps = [(1,2),(1,3),(2,6,7),(2,3,7,9),(2,4,6,8)]
    ls = random.rand(6)
    Ks, eqs = APA(ps,ls,betas,alphas,ws,W,select='all')
    print 'Found %i equilibria'%len(eqs)
    k = 1
    for eq in eqs:
        print 'equlibrium %i --------------'%k
        P = eq[0]
        H1 = eq[1]
        Q = array(eq[2])*100
        H2 = eq[3]
        print 'P:'
        for i in range(len(Ks)):
            if P[i] != 0:
                print Ks[i], P[i]
        print 'Q:'
        print array(map(round,Q))/100.
        print 'H1 = %f, H2 = %f'%(H1,H2)
        k += 1
    print 'elapsed time: %s'%str(time.time()-start) 
    print 'Lemke-Howson:' 
    etimes = []
    for s1 in range(len(Ks)):
        start = time.time()
        Ks, eqs = APA(ps,ls,betas,alphas,ws,W,select='one',s1=s1,verbose=False)
        etime = time.time()-start
        etimes.append(etime)
        print 'elapsed time: %s'%str(time.time()-start)
        eq = eqs[0]
        P = eq[0]
        H1 = eq[1]
        Q = array(eq[2])*100
        H2 = eq[3]
        print 'P:'
        for i in range(len(Ks)):
            if P[i] != 0:
                print Ks[i], P[i]
        print 'Q:'
        print array(map(round,Q))/100.
        print 'H1 = %f, H2 = %f'%(H1,H2)     
    ya,xa = histogram(array(etimes),bins=50)
    ya[0] = 0    
    plt.plot(xa[0:-1],ya)
    plt.show()         

def run(W,b,c,infile,graph=False):
    print ' ========APA=========='
    print time.asctime()  
    print ' ====================='    
    pm=AcquisitionNetwork();
    pm.parseXSLXFile(infile);       
    pm.calcAllPaths();
    pm.sortPathListByAttractiveness();
    
    if graph:
        pm.draw()
    
    pl=pm.getPathList();
    
#  truncate!
    pl=pl[0:50]
    
    print("Total number of paths: %s"%str(len(pl)));
    print "Number of distinct edges: %s"%str(pm.getDistinctEdgeCount())
       
    
    edges = dict()    
    betas = []
    ws = []
    i = 0
    for ap in pl:
        for edge in ap.getEdgeList():
            dct = edge[2]
#            edgestr = edge[0]+':'+edge[1]+':'+dct['semantic']
            edgestr = dct['inspectorateactivitytype']
            if not edges.has_key(edgestr):
                edges[edgestr] = i
                betas.append(1.0-dct['detectionprobability'])
                ws.append(dct['costs'])
                i+=1
    wsasarray=asarray(ws)
    ps = []
    ps_displaystr=[]
    ls = []
    for ap in pl:
        p = []
        l = 0.0
        for edge in ap.getEdgeList():
            dct = edge[2]
#            edgestr = edge[0]+':'+edge[1]+':'+dct['semantic']
            edgestr = dct['inspectorateactivitytype']
            p.append(edges[edgestr])
            l += dct['weight']
        ps.append(p)
        ps_displaystr.append(ap.getDisplayStr())
        ls.append(l)   
        
    alphas = zeros(len(betas))
    
    print "Number of distinct activities: %s \n Hash Table:"%str(pm.getDistinctActivityCount())
    edgeId2ActivityStr=dict()
    for (key,value) in sorted(edges.items(),key=operator.itemgetter(1)):            
        w = str(ws[value])
        dp = str(1-betas[value])
        print 'activity: %s effort: %s  1-beta: %s  %s'%(value,w,dp,key)
        edgeId2ActivityStr[value]=key   
        
  
    start = time.time()
    print '\n\n\nTotal inspection effort: %f'%W
    
    print 'Affordable Inspectorate strategies (at least contained in one strategy):'
    outstring='['        
    for (key,value) in sorted(edges.items(),key=operator.itemgetter(1)):            
        w=ws[value]
        if w<=W:
            outstring=outstring + str(key) + ", "        
    print outstring[0:max(len(outstring)-2,1)]+']'
    
    Ks,eq = APA(ps,ls,betas,alphas,ws,W,b=b,c=c)
    P,H1,Q,H2 = eq[0]
    print 'Nash Equilibrium:'
    print 'Inspectorate equilibrium payoff %f'%H1
    print 'State equilibrium payoff        %f'%H2
    print 'Effectiveness %i percent' %int((c+H1)*(100.0/c))
    
    idx = where(P)[0]
            
    print 'Equilibrium Inspectorate strategy:'
    inspectoratecosts=0.0;
    for i in idx:
        print 'prob: %f path edges: ['%P[i],
        for j in range(0,len(Ks[i])):
            print edgeId2ActivityStr[Ks[i][j]],
            if j<len(Ks[i])-1:
                print ', ',
        print '] ',
        print ' costs: ',
        costs=sum(wsasarray[Ks[i]]);
        print costs
        inspectoratecosts=inspectoratecosts+costs*P[i]
    print 'Inspectorate costs for this equilibrium strategy: %f'%inspectoratecosts
    idx = where(Q)[0]     
    ps.append(0)
    print 'Equilibrium State strategy:'
    for i in idx:
        if ps[i]==0:
            st = 'legal'
        else:
            st = ps_displaystr[i]    
        print 'prob: %f path: [%s]'%(Q[i],st)   
    ps.pop()
    elapsedTime=time.time()-start
    print 'Elapsed time: %f s'%(elapsedTime)

def main():      
    usage = '''
    Usage:
    ------------------------------------------------
        Calculate optimal inspection strategies 
        from acquisition path analysis
        
        python %s [-h] [-g] [-b value] [-c value] Excel_File Inspection_effort
        -h this usage message
        -g draw diversion path graph (default False)
        -b set perceived sanction parameter (default 1)
           (incentive d is 9 for most attractive path)
        -c set inspectorate loss for not detecting legal behavior (default 100)
          (loss a for detecting illegal action is 10)  
    --------------------------------------------'''%sys.argv[0]
    graph = False
    b = 1
    c = 100
    s1 = 0
    options,args = getopt.getopt(sys.argv[1:],'hdb:c:')
    for option, value in options: 
        if option == '-h':
            print usage
            return     
        elif option == '-d':
            graph=True  
        elif option == '-b':
            b = eval(value)   
        elif option == '-c':
            c = eval(value)                    
    if len(args) != 2:
        print 'Incorrect number of arguments'
        print usage
        sys.exit(1)        
    W = float(args[1])
    infile = args[0]
    run(W,b,c,infile,graph)
    
if __name__ == '__main__':
#   main()
    simulate()
    
    