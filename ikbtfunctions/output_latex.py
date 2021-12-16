#!/usr/bin/python
#
#     Classes to generate LaTex outputs
#

# Copyright 2017 University of Washington

# Developed by Dianmu Zhang and Blake Hannaford
# BioRobotics Lab, University of Washington

# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import sympy as sp
import shutil as sh
import os as os
import sys as sys
import pickle
import re 
import ikbtbasics.pykinsym as pks
import ikbtbasics.kin_cl as kc
from   ikbtbasics.solution_graph_v2 import *
import ikbtbasics.matching as mtch

import b3 as b3          # behavior trees

from   ikbtfunctions.helperfunctions import *
import ikbtfunctions.graph2latex as gl
#from kin_cl import *


class LatexFile():
    def __init__(self,fname):
        self.filename = fname + '.tex'
        if self.filename.endswith('.tex.tex'):
            self.filename = self.filename[:-4]
        print('Working with Latex file: ',self.filename)
        self.preamble = [] # list of line strings
        self.sections = [] # list of lists of line strings
        self.close =    []  # list of line strings
        
        f = open('LaTex/IK_preamble.tex','r')
        self.preamble = f.readlines()
        f.close()
        f = open('LaTex/IK_close.tex','r')
        self.close = f.readlines()
        f.close()
        
    def set_title(self,title):        
        self.preamble.append(eol)
        self.preamble.append(('\begin{center} \section*{***TITLE***} \end{center}'+eol).replace(title))

        
    #  optional to override the template file in /LaTex
    def set_preamble(self,str):
        self.preamble = str;
        
        
    #  output the final latex file
    def output(self):
        f = open(self.filename,'w') 
        plines(self.preamble,f)
        for s in self.sections:
            print('\n\n',file=f)
            plines(s,f)
        plines(self.close,f)
        f.close()
        

def plines(sl,f):
    for s in sl:
        print(s,end='',file=f)
     

#
#      Generate a complete report in latex
#
def output_latex_solution(Robot,variables, groups):
    GRAPH = True
    ''' Print out a latex document of the solution equations. '''
    eol = '\n'
    orig_name =  Robot.name.replace('test: ','')
    fixed_name = orig_name.replace(r'_', r'\_')

    DirName = 'LaTex/' 
    fname = DirName + 'ik_solution_'+orig_name+'.tex'
    LF = LatexFile(fname)
    
    ####################   Intro Section
    
    introstring = r'''
    \begin{center}
    \section*{Inverse Kinematic Solution for ''' + fixed_name + r'''}
    \today
    \end{center}
    \section{Introduction}
    This report describes closed form inverse kinematics solutions for '''+fixed_name+r'''.   The solution was generated by 
    the \href{https://github.com/uw-biorobotics/IKBT}{IK-BT package}
    from the University of Washington Biorobotics Lab.
    The IK-BT package is described in
    \url{https://arxiv.org/abs/1711.05412}.  
    IK-BT derives your  equations
    using {\tt Python 3.8} and the {\tt sympy 1.9} module for symbolic mathematics.
    '''
    
    LF.sections.append(introstring.splitlines())
    
    ####################   Kinematic params
    
    paramsection = r'''\section{Kinematic Parameters}
    The kinematic parameters for this robot are
    \[ \left [ \alpha_{i-1}, \quad a_{i-1}, \quad d_i, \quad \theta_i \right  ] \]
    \begin{dmath}''' + sp.latex(Robot.Mech.DH) +  r'\end{dmath}'
    
    LF.sections.append(paramsection.splitlines())
    
    
    
    
    ####################  Forward Kinematics

    fksection = r'''\section{Forward Kinematic Equations}
    The forward kinematic equations for this robot are:'''+eol

    fksection += r'\begin{dmath} '+eol

    LHS = ik_lhs()
    RHS = kc.notation_squeeze(Robot.Mech.T_06)   # see kin_cl.mechanism.T_06
    
    fksection += sp.latex(LHS) + r' \\'+eol 
    
    COLUMNS = True
    if COLUMNS:
        for c in range(4):
            fksection +=  r'\mathrm{Column \quad'+str(c+1)+'}' +eol+sp.latex(RHS[:,c]) + r'\\'+eol 
    else:
        fksection += sp.latex(RHS)
    fksection += r'\end{dmath}'+eol

    fksection += 'Note: column numbers use math notation rather than python indeces.'+eol
    
    LF.sections.append(fksection.splitlines())

    ####################   Unknowns
    
    unksection = r'\section{Unknown Variables: }'+eol
    
    # introduce the unknowns and the solution ORDER
    unksection += r'''The unknown variables for this robot are (in solution order): ''' +eol+r'\begin{enumerate}'+eol

    tvars = {}
    for v in variables:
        tvars[v]=v.solveorder
    for v in sorted(tvars, key=tvars.get):
        tmp = '$' + sp.latex(v) + '$'
        tmp = tmp.replace(r'th_', r'\theta_')
        tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {}
        unksection += eol+r'\item {'+tmp+'}'
                                 
    unksection += r'\end{enumerate}'+eol

    LF.sections.append(unksection.splitlines())
    
    
    ####################   Solutions to IK
    
    solsection = r'\section{Solutions} '+eol
    solsection += ''' The following equations comprise the full solution set for this robot.''' + eol

    # sort the nodes into solution order
    sorted_node_list = sorted(Robot.solution_nodes)

    for node in sorted_node_list: 
        if node.solvemethod != '*None*':   # skip variables (typically extra SOA's) that are not used.
            ALIGN = True
            tmp = '$' + sp.latex(node.symbol) + '$'
            tmp = tmp.replace(r'th_', r'\theta_')
            tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {} for latex
            solsection += r'\subsection{'+tmp+r' } '+eol + 'Solution Method: ' + node.solvemethod + eol
            
            if (ALIGN):
                solsection += r'\begin{align}'+eol
            else:
                solsection += r'\begin{dmath} '+eol
            i=0
            nsolns = len(node.solution_with_notations.values())
            for eqn in node.solution_with_notations.values():
                i += 1
                if ALIGN and (i < nsolns):
                    tmp2 = r'\\'   # line continuation for align environment
                else:
                    tmp2 = ''
                tmp = str(eqn.LaTexOutput(ALIGN))
                # convert division ('/') to \frac{}{} for nicer output
                if re.search(r'/',tmp):
                    tmp = tmp.replace(r'(.+)=(.+)/(.+)', r'\1 = \frac{\2}{\3}')
                solsection += tmp + ' '+ tmp2

            if (ALIGN):
                solsection += r'\end{align} '+eol
            else:
                solsection += r'\end{dmath} '+eol
                
            solsection += eol+eol

    LF.sections.append(solsection.splitlines())
    
    ####################  List the edges of the solution graph
    
    edgesection = r'\section{Solution Graph (Edges)} '+eol  +  r'''
The following is the abstract representation of solution graph for this manipulator (nodes with parent -1 are roots).  Future: graphic representation. :
\begin{verbatim}
'''
    
    graph = Robot.notation_graph

    i = 0
    sameline = '     '
    sepstr = sameline
    print('test: Starting Graph output')
    for edge in graph:
        i+=1
        if i%2==0:
            sepstr = eol
        elif i>1:
            sepstr = sameline
        print('test: edge + sepstr: [',str(edge)+sepstr,']')
        edgesection+= str(edge)+ sepstr
        
    edgesection +=  r'\end{verbatim} '+eol
    
    LF.sections.append(edgesection)
    
    
    ####################  Solution Sets
    
    solsection = r'\section{Solution Sets}'+eol
    solsection += r'''
The following are the sets of joint solutions (poses) for this manipulator:
\begin{verbatim}
    '''
    
    # groups = mtch.matching_func(Robot.notation_collections, Robot.solution_nodes)

    i=0
    for g in groups:
        solsection += str(g)+eol

    solsection += '\end{verbatim}'+eol+eol
    
    ####################  Solution methods
     # Equations evaluated (for result verification or debugging)
    metsection = r'\section{Equations Used for Solutions}'

    for node in sorted_node_list:
        if node.solvemethod == '*None*':  # skip unused SOA vars. 
            continue
                #print out the equations evaluated
        # print  'Equation(s):
        tmp = '$' + sp.latex(node.symbol) + '$'
        tmp = tmp.replace(r'th_', r'\theta_')
        tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {} for latex
        metsection += r'\subsection{'+tmp+' }'+eol
        metsection += r'Solution Method: '+node.solvemethod

        for eqn in node.eqnlist:
            metsection += r'\begin{dmath}'+eol
            metsection += eqn.LaTexOutput()+eol
            metsection += r'\end{dmath}'+eol

    LF.sections.append(metsection.splitlines())
    
     
    ####################  Jacobian Matrix
    
    jsection =r'''\newpage 
\section{Jacobian Matrix}

'''
    
    j66result = kc.notation_squeeze(Robot.Mech.J66)
    cols = j66result.shape[1]
    
    jsection += r'\begin{dmath}'+eol
    jsection += '^6J_6  = '+r'\\'+eol
    
    COLUMNS = True
    if COLUMNS:
        for c in range(cols):
            jsection += r'\mathrm{'+ r' Column \quad'+str(c+1)+ r'}\\'+eol
            jsection += sp.latex(j66result[:,c])+eol
            jsection += r'\\ '+eol
    else:
        jsection += sp.latex(j66result)+eol
    jsection += r'\end{dmath}'+eol
    
    LF.sections.append(jsection.splitlines())
    
    # Write out the file!!
    LF.output()

#
#
#################################################################################
#
#
#
#      Generate a partial report: only the FK and Jacobian
#
def output_FK_equations(Robot):
    GRAPH = True
    ''' Print out a latex document of the solution equations. '''
    eol = '\n'
    orig_name =  Robot.name.replace('test: ','')
    fixed_name = orig_name.replace(r'_', r'\_')

    DirName = 'LaTex/' 
    fname = DirName + 'fk_equations_'+orig_name+'.tex'
    LF = LatexFile(fname)
    
    ####################   Intro Section
    
    introstring = r'''
    \begin{center}
    \section*{Forward Kinematic Computations for ''' + fixed_name + r'''}
    \today
    \end{center}
    \section{Introduction}
    This report gives the forward kinematics solutions for '''+fixed_name+r'''.
    These equations are automatically generated by the \href{https://github.com/uw-biorobotics/IKBT}{IK-BT package}
    from the University of Washington Biorobotics Lab.
    The IK-BT package is described in
    \url{https://arxiv.org/abs/1711.05412}.  
    IK-BT derives your inverse kinematics equations
    using {\tt Python 3.8} and the {\tt sympy 1.9} module for symbolic mathematics.
    '''
    
    LF.sections.append(introstring.splitlines())
    
    ####################   Kinematic params
    
    paramsection = r'''\section{Kinematic Parameters}
    The kinematic parameters for this robot are
    \[ \left [ \alpha_{i-1}, \quad a_{i-1}, \quad d_i, \quad \theta_i \right  ] \]
    \begin{dmath}''' + sp.latex(Robot.Mech.DH) +  r'\end{dmath}'
    
    LF.sections.append(paramsection.splitlines())  
    
    ####################  Forward Kinematics

    fksection = r'''\section{Forward Kinematic Equations}
    The forward kinematic equations for this robot are:'''+eol

    fksection += r'\begin{dmath} '+eol

    LHS = ik_lhs()
    RHS = kc.notation_squeeze(Robot.Mech.T_06)   # see kin_cl.mechanism.T_06
    
    fksection += sp.latex(LHS) + r'= \\'+eol 
    
    COLUMNS = True
    if COLUMNS:
        for c in range(4):
            fksection += r'\mathrm{Column \quad'+str(c+1)+r'}\\'+eol+sp.latex(RHS[:,c]) + r'\\'+eol 
    else:
        fksection += sp.latex(RHS)
    fksection += r'\end{dmath}'+eol

    fksection += 'Note: column numbers use math notation rather than python indeces.'+eol
    
    LF.sections.append(fksection.splitlines())

    
     
    ####################  Jacobian Matrix
    
    jsection =r'''\newpage 
\section{Jacobian Matrix}

'''
    
    j66result = kc.notation_squeeze(Robot.Mech.J66)
    cols = j66result.shape[1]
    
    jsection += r'\begin{dmath}'+eol
    jsection += r'^6J_6  = \\'+eol
    
    COLUMNS = True
    if COLUMNS:
        for c in range(cols):
            jsection += r'\mathrm{Column \quad '+str(c+1)+r'}\\'+eol
            jsection += sp.latex(j66result[:,c])+eol
            jsection += r'\\ '+eol
    else:
        jsection += sp.latex(j66result)+eol
    jsection += r'\end{dmath}'+eol
    
    LF.sections.append(jsection.splitlines())
    
    # Write out the file!!
    LF.output()