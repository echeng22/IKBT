
#
#      Generate a complete report in latex
#
def output_latex_solution(Robot,variables, groups):
    GRAPH = True
    ''' Print out a latex document of the solution equations. '''

    orig_name =  Robot.name.replace('test: ','')
    fixed_name = orig_name.replace(r'_', r'\_')

    DirName = 'LaTex/'
    defaultname = DirName + 'IK_solution.tex'
    fname = DirName + 'IK_solution_'+orig_name+'.tex'
    f = open(fname, 'w')
    print(r'''
    \begin{center}
    \section*{Inverse Kinematic Solution for ''' + fixed_name + r'''}
    \today
    \end{center}
    \section{Introduction}
    This report describes closed form inverse kinematics solutions for '''+fixed_name+r'''.
    The solution was automatically generated by the IK-BT package from the University of Washington Biorobotics Lab.
    The IK-BT package is described in
    \url{https://arxiv.org/abs/1711.05412}.  IK-BT derives your inverse kinematics equations
    using {\tt Python 2.7} and the {\tt sympy} module for symbolic mathematics.
    ''',file=f)
    
    
    print(r'''\section{Kinematic Parameters}
    The kinematic parameters for this robot are
    \[ \left [ \alpha_{i-1}, \quad a_{i-1}, \quad d_i, \quad \theta_i \right  ] \]
    \begin{dmath}''', file=f),
    print(sp.latex(Robot.Mech.DH),file=f),
    print('''\end{dmath}
    ''',file=f)



    print(r'''\section{Forward Kinematic Equations}
    The forward kinematic equations for this robot are:''',file=f)


    LHS = ik_lhs()
    RHS = kc.notation_squeeze(Robot.Mech.T_06)   # see kin_cl.mechanism.T_06
    print(r'\begin{dmath}', file=f)
    print(sp.latex(LHS) + r' =  \\', file=f)
    COLUMNS = True
    if COLUMNS:
        for c in range(4):
            print(r'\mathrm{'+'Column  {:}'.format(c)+r'}', file=f)
            print(sp.latex(RHS[:,c]),file=f)
            print(r'\\',file=f)
    else:
        print(sp.latex(RHS), file=f)
    print(r'\end{dmath}', file=f)

    print(r'\section{Unknown Variables: }', file=f)

    # introduce the unknowns and the solution ORDER
    print('''The unknown variables for this robot are (in solution order): ''', file=f)
    print(r'\begin{enumerate}', file=f)

    tvars = {}
    for v in variables:
        tvars[v]=v.solveorder
    for v in sorted(tvars, key=tvars.get):
        tmp = '$' + sp.latex(v) + '$'
        tmp = tmp.replace(r'th_', r'\theta_')
        tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {}
        print('\item {'+tmp+'}', file=f)
    print(r'\end{enumerate}', file=f)



    # print the solutions for each variable (in DH order)
    print(r'\section{Solutions}', file=f)
    print(''' The following equations comprise the full solution set for this robot.''', file=f)

    # sort the nodes into solution order
    sorted_node_list = sorted(Robot.solution_nodes)

    for node in sorted_node_list: 
        if node.solvemethod != '*None*':   # skip variables (typically extra SOA's) that are not used.
            ALIGN = True
            tmp = '$' + sp.latex(node.symbol) + '$'
            tmp = tmp.replace(r'th_', r'\theta_')
            tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {} for latex
            print(r'\subsection{'+tmp+' }', file=f)
            print( 'Solution Method: ', node.solvemethod, file=f)
            
            if (ALIGN):
                print(r'\begin{align}', file=f)
            else:
                print(r'\begin{dmath}', file=f)
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
                print(tmp, tmp2, file=f)

            if (ALIGN):
                print(r'\end{align}', file=f)
            else:
                print(r'\end{dmath}', file=f)

    ###########################################################
    #
    #   Future:  Output a graph of the solution dependencies
    #            (not a tree!)
    #
    ###########################################################
    print(r'\section{Solution Graph (Edges)}', file=f)
    print(r'''
    The following is the abstract representation of solution graph for this manipulator (nodes with parent -1 are roots):
    \begin{verbatim}
    ''', file=f)
    graph = Robot.notation_graph

    for edge in graph:
        print(edge, file=f)

    print('\end{verbatim}', file=f)
    ###########################################################
    #
    #   Output of solution sets
    #
    ###########################################################

    print(r'\section{Solution Sets}', file=f)
    print(r'''
    The following are the sets of joint solutions (poses) for this manipulator:
    \begin{verbatim}
    ''', file=f)
    # groups = mtch.matching_func(Robot.notation_collections, Robot.solution_nodes)

    for g in groups:
        print(g, file=f)

    print('\end{verbatim}', file=f)

    ###########################################################
    #
    #   Output of Equation Evaluated (Use for verification or debugging)
    #
    ###########################################################
    #################################################
    # Equations evaluated (for result verification or debugging)
    print(r'\section{Equations Used for Solutions}', file=f)



    for node in sorted_node_list:
        if node.solvemethod == '*None*':  # skip unused SOA vars. 
            continue
                #print out the equations evaluated
        # print  'Equation(s):
        tmp = '$' + sp.latex(node.symbol) + '$'
        tmp = tmp.replace(r'th_', r'\theta_')
        tmp = re.sub(r'_(\d+)',  r'_{\1}', tmp)   # get all digits of subscript into {} for latex
        print(r'\subsection{'+tmp+' }', file=f)
        print('Solution Method: ', node.solvemethod, file=f)

        for eqn in node.eqnlist:
            print(r'\begin{dmath}', file=f)
            print(eqn.LaTexOutput(), file=f)
            print(r'\end{dmath}', file=f)


    ###########################################################################
    #Appendix:
    #
    #   Output Jacobian Matrix, J66
    #
    ############################################################################
    if True:
        print(r'''\newpage 
\section{Jacobian Matrix}

''', file = f)
        
        j66result = kc.notation_squeeze(Robot.Mech.J66)
        cols = j66result.shape[1]
        
        print(r'\begin{dmath}', file=f)
        print(r'^6J_6  = \\', file=f)
        
        COLUMNS = True
        if COLUMNS:
            for c in range(cols):
                print(r'\mathrm{'+ r'Column \quad {:}'.format(c)+r'}\\', file=f)
                print(sp.latex(j66result[:,c]),file=f)
                print(r'\\',file=f)
        else:
            print(sp.latex(j66result), file=f)
        print(r'\end{dmath}', file=f)
        
        
    f.close()

    # copy file to default filename (processing of latex simplifier)
    #  after this step  >pdflatex ik_report_template.tex   <<JUST WORKS!>>

    sh.copyfile(fname, defaultname)
#
#  ###########   End of Latex Output Section
#