# __________________________________
from flask import Flask
import ghhops_server as hs
from ghhops_server.params import HopsBoolean, HopsNumber, HopsPoint, HopsString
import rhino3dm
import random as rnd
# __________________________________
import numpy as np
import matlab.engine
eng = matlab.engine.start_matlab()
# __________________________________
# register hops app as middleware
app = Flask(__name__)
hops: hs.HopsFlask = hs.Hops(app)
# __________________________________

############################################################################
# Hops Running Check
############################################################################

@ hops.component(
    "/random",
    name="Random",
    nickname="Random",
    description="Create random points",
    inputs=[
        hs.HopsNumber("Random N", "N", "Number of random points to generate")
    ],
    outputs=[hs.HopsPoint("Point", "P", "Random Points")]
)
def random(numb):
    ptlist = []
    numb = int(numb)
    for i in range(numb):
        x = rnd.random()
        y = rnd.random()
        z = rnd.random()
        pt = rhino3dm.Point3d(x, y, z)
        ptlist.append(pt)
    return ptlist


############################################################################
# Matlab Running Check
############################################################################


@hops.component(
    "/add",
    name="Matlab Add",
    nickname="M Add",
    description="Add numbers with CPython using MatlabAPI",
    icon="icon\matlab.png",
    inputs=[
        hs.HopsNumber("A", "A", "First number"),
        hs.HopsNumber("B", "B", "Second number"),
    ],
    outputs=[hs.HopsNumber("Ans", "A", "Answer")]
)
def add(a: float, b: float):
    ans = eng.matlab_add(a, b)
    return ans


@hops.component(
    "/mult",
    name="Matlab Multiply",
    nickname="M Mult",
    description="Multiply numbers with CPython using MatlabAPI",
    icon="icon\matlab.png",
    inputs=[
        hs.HopsNumber("A", "A", "First number"),
        hs.HopsNumber("B", "B", "Second number"),
    ],
    outputs=[hs.HopsNumber("Ans", "A", "Answer")]
)
def mult(a: float, b: float):
    ans = eng.matlab_mult(a, b)
    return ans


############################################################################
# PDE 2D
############################################################################


@hops.component(
    "/PDE_2D",
    name="Matlab PDE 2D",
    nickname="M PDE 2D",
    description="Compute Thermal Partial Differential Equation with CPython using MatlabAPI",
    icon="icon\matlab_PDE_2D.png",
    inputs=[
        hs.HopsBoolean("PDE Mode", "PDE M",  # 0
                       "True=Steady State, False=Transient"),
        hs.HopsString("File", "F", "Importing Mesh File"),  # 1
        # hs.HopsNumber('HMin', 'Min', 'Min mesh length'),  # 2
        hs.HopsNumber("HMax", 'Max', "Max mesh length"),  # 3
        hs.HopsNumber('Therm Conductivity', 'TPTC',
                      'Thermal Conductivity of the material in W/Km'),  # 4
        hs.HopsNumber('Mass Denssity', 'TPMD',
                      'Mass Density of the material in kg/m^3'),  # 5
        hs.HopsNumber(
            'Thermal BC', 'TBC', 'TBC temp flux input mode. 0=tt, 1=tf, 2=ft, 3=ff'),  # 6
        hs.HopsPoint('Point1', 'P1', "Point to find 1st edge ID"),  # 7
        hs.HopsPoint('Point2', 'P2', "Point to find 2nd edge ID"),  # 8
        hs.HopsNumber("Temp1", 'T1', 'Temperature of 1st edge in Kelvin'),  # 9
        hs.HopsNumber(
            "Temp2", 'T2', 'Temperature of 2nd edge in Kelvin'),  # 10
        hs.HopsNumber("Step", "S", "Compute Step Amount"),  # 11
        hs.HopsNumber("Count", "C", "Compute Step Count")  # 12
    ],
    outputs=[
        hs.HopsNumber("Time", "T", "Compute Tic Toc"),
        hs.HopsPoint("Vertex", "V", "Regenerated Mesh Vertex"),
        hs.HopsString(
            "Temp", "T", "Temperature. Use split text for transient mode"),
        hs.HopsNumber("Average Temp", "Avr",
                      "Average Temperature of each phase"),
        hs.HopsString(
            "QX", "QX", "Vector X of Heat Flux. Use split text for transient mode"),
        hs.HopsString(
            "QY", "QY", "Vector Y of Heat Flux. Use split text for transient mode")
    ]
)
def pde2d(pde_bool, file_name, hmax, tp_tcv, tp_dv, tbc, p1, p2, t1, t2, ss, sn):
    # __________________________
    # Convert rhino3dm Point3d to python [1,2]array
    c1 = []
    c1.append(p1.X)
    c1.append(p1.Y)
    # __________________________
    c2 = []
    c2.append(p2.X)
    c2.append(p2.Y)
    # __________________________
    time, node, ev_t, qx, qy = eng.matlab_2d(
        pde_bool, file_name, hmax, tp_tcv, tp_dv, tbc, c1, c2, t1, t2, ss, sn, nargout=5)
    # __________________________
    node_np = np.array(node)
    node_tp = node_np.transpose(1, 0)
    node_list = node_tp.tolist()
    # __________________________
    pt_list = []
    for p in node_list:
        x = p[0]
        y = p[1]
        pt = rhino3dm.Point3d(x, y, 0)
        pt_list.append(pt)
    # _______________________
    sep = ','
    # _______________________
    ev_t_np = np.array(ev_t)
    ev_t_str = ev_t_np.astype(str)
    ev_t_list = ev_t_str.tolist()

    ev_t_data = []
    for t in ev_t_list:
        data = sep.join(t)
        ev_t_data.append(data)
    # __________________________
    t_tp = ev_t_np.transpose()
    t_av = np.average(t_tp, axis=1)
    t_av_data = t_av.tolist()
    # __________________________
    qx_np = np.array(qx)
    qx_str = qx_np.astype(str)
    qx_list = qx_str.tolist()

    qx_data = []
    for qx in qx_list:
        data = sep.join(qx)
        qx_data.append(data)
    # __________________________
    qy_np = np.array(qy)
    qy_str = qy_np.astype(str)
    qy_list = qy_str.tolist()

    qy_data = []
    for qy in qy_list:
        data = sep.join(qy)
        qy_data.append(data)
    # __________________________

    return (time, pt_list, ev_t_data, t_av_data, qx_data, qy_data)

############################################################################
# PDE3D
############################################################################


@hops.component(
    "/PDE_3D",
    name="Matlab PDE 3D",
    nickname="M PDE 3D",
    description="Compute Thermal Partial Differential Equation with CPython using MatlabAPI",
    icon="icon\matlab_PDE_3D.png",
    inputs=[
        hs.HopsBoolean(
            "Mode", "M", "PDE thermal compute mode, True=Steady State, False=Transient"),  # 0
        hs.HopsString("File", "F", "Importing Mesh File"),  # 1
        hs.HopsNumber("HMax", "Max", "Mesh Generating Max Distance"),  # 2
        hs.HopsNumber('Therm Conductivity', 'TPTC',
                      'Thermal Conductivity of the material in W/Km'),  # 4
        hs.HopsNumber('Mass Denssity', 'TPMD',
                      'Mass Density of the material in kg/m^3'),  # 5
        hs.HopsNumber('Thermal Boundary Condition', 'TBC',
                      'TBC temp flux input mode. 0=tt, 1=tf, 2=ft, 3=ff'),  # 3
        hs.HopsPoint('Point1', 'P1', "Point to find 1st edge ID"),  # 4
        hs.HopsPoint('Point2', 'P2', "Point to find 2nd edge ID"),  # 5
        hs.HopsNumber("Temp1", 'T1', 'Temperature of 1st edge in Kelvin'),  # 6
        hs.HopsNumber(
            "Temp2", 'T2', 'Temperature of 2nd edge in Kelvin'),  # 7
        hs.HopsNumber("Step", "S", "Compute Step Amount"),  # 8
        hs.HopsNumber("Count", "C", "Compute Step Count")  # 9
    ],
    outputs=[
        hs.HopsNumber("Time", "T", "Compute Tic Toc"),
        hs.HopsPoint("Vertex", "V", "Regenerated Mesh Vertex"),
        hs.HopsString("Temp", "T", "Temperature"),
        hs.HopsNumber("Average Temp", "Avr",
                      "Average Temperature of each phase"),
        hs.HopsString("QX", "QX", "Vector X of Heat Flux"),
        hs.HopsString("QY", "QY", "Vector Y of Heat Flux"),
        hs.HopsString("QZ", "QZ", "Vector Z of Heat Flux")
    ]
)
def pde3d(pde_bool: bool, mesh_file: str, hmax, tp_tcv, tp_dv, tbc, p1, p2, temp1, temp2, ss: float, sn: int):

    c1 = []
    c2 = []

    c1.append(p1.X)
    c1.append(p1.Y)
    c1.append(p1.Z)

    c2.append(p2.X)
    c2.append(p2.Y)
    c2.append(p2.Z)

    # __________________________
    time, node, ev_t, qx, qy, qz = eng.matlab_3d(
        pde_bool, mesh_file, hmax, tp_tcv, tp_dv, tbc, c1, c2, temp1, temp2, ss, sn, nargout=6)
    # __________________________
    node_np = np.array(node)
    node_tp = node_np.transpose(1, 0)
    node_list = node_tp.tolist()
    # __________________________
    pt_list = []
    for p in node_list:
        x = p[0]
        y = p[1]
        z = p[2]
        pt = rhino3dm.Point3d(x, y, z)
        pt_list.append(pt)
    # _______________________
    sep = ','
    # _______________________
    ev_t_np = np.array(ev_t)
    ev_t_str = ev_t_np.astype(str)
    ev_t_list = ev_t_str.tolist()

    ev_t_data = []
    for t in ev_t_list:
        data = sep.join(t)
        ev_t_data.append(data)
    # __________________________
    t_tp = ev_t_np.transpose()
    t_av = np.average(t_tp, axis=1)
    t_av_data = t_av.tolist()
    # __________________________
    qx_np = np.array(qx)
    qx_str = qx_np.astype(str)
    qx_list = qx_str.tolist()

    qx_data = []
    for qx in qx_list:
        data = sep.join(qx)
        qx_data.append(data)
    # __________________________
    qy_np = np.array(qy)
    qy_str = qy_np.astype(str)
    qy_list = qy_str.tolist()

    qy_data = []
    for qy in qy_list:
        data = sep.join(qy)
        qy_data.append(data)
    # __________________________

    qz_np = np.array(qz)
    qz_str = qz_np.astype(str)
    qz_list = qz_str.tolist()

    qz_data = []
    for qz in qz_list:
        data = sep.join(qz)
        qz_data.append(data)
    # __________________________

    return (time, pt_list, ev_t_data, t_av_data, qx_data, qy_data, qz_data)


############################################################################
# input multiple
############################################################################

@hops.component(
    "/list_access",
    name="List Access",
    nickname="LstAcc",
    description="get list of numbers",
    inputs=[
        hs.HopsPoint("Point","P","List of Points",hs.HopsParamAccess.LIST),
        hs.HopsString("Mode", "M", "List of Modes", hs.HopsParamAccess.LIST),
        hs.HopsNumber("Temperature", "T", "List of numbers", hs.HopsParamAccess.LIST)
    ],
    outputs=[
        hs.HopsString("A"),
        hs.HopsString("B"),
        hs.HopsString("C")
        ]
)
def nums(P_in, M_in, T_in):
    pt_list = []
    for p in P_in:
        x = p.X
        y = p.Y
        z = p.Z
        pt = [x,y,z]
        pt_list.append(pt)
    
    a,b = eng.matlab_pass(pt_list,nargout=2)
    c,d = eng.matlab_pass(M_in,nargout=2)
    e,f = eng.matlab_pass(T_in,nargout=2)

    A = a
    B = c
    C = e

    return (A,B,C)


############################################################################
# 
############################################################################

############################################################################
# input multiple
############################################################################

@hops.component(
    "/PDE_2D_Mult",
    name="PDE 2D Multy Inputs",
    nickname="PDE 2D M",
    description="Compute Thermal Partial Differential Equation with CPython using MatlabAPI",
    icon="icon\matlab_PDE_2D.png",
    inputs=[
        hs.HopsBoolean(
            "Mode", "M", "PDE thermal compute mode, True=Steady State, False=Transient"),  # 0
        hs.HopsString("File", "F", "Importing Mesh File"),  # 1
        hs.HopsNumber("HMax", "Max", "Mesh Generating Max Distance"),  # 2
        hs.HopsNumber('Therm Conductivity', 'TPTC',
                      'Thermal Conductivity of the material in W/Km'),  # 4
        hs.HopsNumber('Mass Denssity', 'TPMD',
                      'Mass Density of the material in kg/m^3'),  # 5

        hs.HopsPoint("Point","P","List of Points",hs.HopsParamAccess.LIST),
        hs.HopsString("Heat Mode", "H", "List of Modes", hs.HopsParamAccess.LIST),
        hs.HopsNumber("Temperature", "T", "List of numbers", hs.HopsParamAccess.LIST),

        hs.HopsNumber("Step", "S", "Compute Step Amount"),  # 8
        hs.HopsNumber("Count", "C", "Compute Step Count")  # 9
    ],
    outputs=[
        hs.HopsNumber("Time", "T", "Compute Tic Toc"),
        hs.HopsPoint("Vertex", "V", "Regenerated Mesh Vertex"),
        hs.HopsString(
            "Temp", "T", "Temperature. Use split text for transient mode"),
        hs.HopsNumber("Average Temp", "Avr",
                      "Average Temperature of each phase"),
        hs.HopsString(
            "QX", "QX", "Vector X of Heat Flux. Use split text for transient mode"),
        hs.HopsString(
            "QY", "QY", "Vector Y of Heat Flux. Use split text for transient mode")
        ]
)
def pde_2d(pde_bool,file_name,hmax,tp_tcv, tp_dv, pts, mode_in,temp_in,ss, sn):

    # __________________________
    pts_list = []
    data_len = len(pts)
    for pt in pts:
        coord = [pt.X, pt.Y]
        pts_list.append(coord)
    # __________________________

    time,qx,qy,node,ev_t = eng.matlab_2d_mult(pde_bool,file_name,hmax,tp_tcv,tp_dv,data_len,pts_list,mode_in,temp_in,ss,sn,nargout=5)

    # __________________________
    node_np = np.array(node)
    node_tp = node_np.transpose(1, 0)
    node_list = node_tp.tolist()
    # __________________________
    pt_list = []
    for p in node_list:
        x = p[0]
        y = p[1]
        pt = rhino3dm.Point3d(x, y, 0)
        pt_list.append(pt)
    # _______________________
    sep = ','
    # _______________________
    ev_t_np = np.array(ev_t)
    ev_t_str = ev_t_np.astype(str)
    ev_t_list = ev_t_str.tolist()

    ev_t_data = []
    for t in ev_t_list:
        data = sep.join(t)
        ev_t_data.append(data)
    # __________________________
    t_tp = ev_t_np.transpose()
    t_av = np.average(t_tp, axis=1)
    t_av_data = t_av.tolist()
    # __________________________
    qx_np = np.array(qx)
    qx_str = qx_np.astype(str)
    qx_list = qx_str.tolist()

    qx_data = []
    for qx in qx_list:
        data = sep.join(qx)
        qx_data.append(data)
    # __________________________
    qy_np = np.array(qy)
    qy_str = qy_np.astype(str)
    qy_list = qy_str.tolist()

    qy_data = []
    for qy in qy_list:
        data = sep.join(qy)
        qy_data.append(data)
    # __________________________

    return (time, pt_list, ev_t_data, t_av_data, qx_data, qy_data)






if __name__ == "__main__":
    app.run(debug=True)
