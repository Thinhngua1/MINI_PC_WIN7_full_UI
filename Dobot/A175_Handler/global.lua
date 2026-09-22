b = 0
a = 0
i = 0
Caotray_output = 0
k = 0
Caotray_input = 0
b2 = 0 
movemode = {movj = 1, movl = 2, movjio = 3, movlio = 4, relmovj = 5, relmovl = 6}
--  Pallet

--直线位置线性插值
function lineInter(position1,position2,n,result)
	dx = (position2[1] - position1[1])/(n-1)
	dy = (position2[2] - position1[2])/(n-1)
	dz = (position2[3] - position1[3])/(n-1)
	for i = 1,n do
	    result[i] = {}
	    result[i][1] = position1[1] + dx*(i-1)  
	    result[i][2] = position1[2] + dy*(i-1)    
	    result[i][3] = position1[3] + dz*(i-1)  
	end
end

--四轴姿态线性插值
function rotInter(p,q,n,result)
   dleta_rz = (q - p)/(n-1);
   --result = {}
   for i = 1,n do
      result[i] = p + dleta_rz*(i-1)
   end
   
end
--生成直线路径点
function buildLine(startPoint,endPoint,counts,pointArray)
	 p1 = {}
	 p1[1] = startPoint["coordinate"][1]
	 p1[2] = startPoint["coordinate"][2]
	 p1[3] = startPoint["coordinate"][3]
	 r1 = startPoint["coordinate"][4]
	 p2 = {}
	 p2[1] = endPoint["coordinate"][1]
	 p2[2] = endPoint["coordinate"][2]
	 p2[3] = endPoint["coordinate"][3]
	 r2 = endPoint["coordinate"][4]
	 --位置线性插补
	 posArray = {}   --位置插值序列
	 rotArray = {}   --姿态插值序列
	 lineInter(p1,p2,counts[1],posArray)
	 rotInter(r1,r2,counts[1],rotArray)
	 --形成标准点位
	 for i=1,#posArray do
	     pointArray[i] = {armOrientation="left",coordinate={},joint={},user=0,tool=0}
	     pointArray[i]["armOrientation"] = startPoint["armOrientation"]
	     pointArray[i]["user"] = startPoint["user"]
	     pointArray[i]["tool"] = startPoint["tool"]
	     pointArray[i]["joint"][1] = startPoint["joint"][1]
	     pointArray[i]["joint"][2] = startPoint["joint"][2]
	     pointArray[i]["joint"][3] = startPoint["joint"][3]
	     pointArray[i]["joint"][4] = startPoint["joint"][4]
	     pointArray[i]["coordinate"][1] = posArray[i][1]
	     pointArray[i]["coordinate"][2] = posArray[i][2]
	     pointArray[i]["coordinate"][3] = posArray[i][3]
	     pointArray[i]["coordinate"][4] = rotArray[i]
	 end
end

--生成平面路径点
function buildPlane(teachArray,counts,pointArray)
	 --生成两个纵列点位L14 L23
	 count1={}
	 count2={}
	 count1[1]=counts[1]  --横长
	 count2[1]=counts[2]  --竖长
	 L14 = {}
	 buildLine(teachArray[1],teachArray[4],count2,L14)
	 L23 = {}
	 buildLine(teachArray[2],teachArray[3],count2,L23)
	 L = {}
	 for i=1,counts[2] do	     
	     buildLine(L14[i],L23[i],count1,L)
	     for j=1,counts[1] do
	     	 pointArray[(i-1)*counts[1]+j] = L[j]
	     end
	 end
end

--count[1]表示横长度
--count[2]表示竖长度
--count[3]表示高长度
--生成立体路径点
function buildVolume(teachArray,counts,VolumeArray)
	 --生成高度点位
	 count_height={}
	 count_height[1]=counts[3]
	 L15 = {}
	 buildLine(teachArray[1],teachArray[5],count_height,L15)
	 L26 = {}
	 buildLine(teachArray[2],teachArray[6],count_height,L26)
	 L37 = {}
	 buildLine(teachArray[3],teachArray[7],count_height,L37)
	 L48 = {}
	 buildLine(teachArray[4],teachArray[8],count_height,L48)
	 counts_plane ={counts[1],counts[2]}
	 planeArray={}
	 for i = 1, counts[3] do
	     plane={L15[i],L26[i],L37[i],L48[i]}
	     buildPlane(plane,counts_plane,planeArray)
	     for j=1,counts[1]*counts[2] do
	     	 VolumeArray[(i-1)*counts[1]*counts[2]+j] = planeArray[j]
	     end
	 
	 end
end

function PalletCreate(teachPoints, counts, resultArray)
	 --一维托盘
	 if (#counts == 1) then
	    buildLine(teachPoints[1],teachPoints[2],counts,resultArray)
	 --二维托盘
	 elseif(#counts == 2) then
	       buildPlane(teachPoints,counts,resultArray)
	 --三维托盘
	 elseif(#counts == 3) then
	       buildVolume(teachPoints,counts,resultArray)
	 else
	 print("Counts Error")
	 end
end

function Systime_correct()
	current_time = Systime() // 1000 - 52*60
end
function pseudo_pause()
  pauseFlag = true
  while DI(1) == 0 do
    Sleep(50)
  end
  pauseFlag = false
end
function MoveReadIO(mode, point, options, IO) 
  if mode == 1 then MovJ(point, options)
  elseif mode == 2 then MovL(point, options)
  elseif mode == 3 then MovJIO(point, IO, options)
  elseif mode == 4 then MovLIO(point, IO, options)
  elseif mode == 5 then RelMovJ(point)
  elseif mode == 6 then RelMovL(point)
  end
  if pauseFlag then
    pseudo_pause()
  end
end
function Input()
  local points_Input = {}
  PalletCreate({P3,P4,P5,P6},{3,2},points_Input)
MovJ(P2)
MoveReadIO(movemode.movj, RelPoint(points_Input[a], {0, 0, 20+(1-i)*Caotray_input, 0}))
MoveReadIO(movemode.relmovl, {0, 0, -20, 0})
Vaccumon( )
Sync()
MoveReadIO(movemode.relmovl, {0, 0, 20, 0})
a = a + 1
MoveReadIO(movemode.movj, P2, {CP = 100})
Sync()
end

function Output()
  local points_Output1_24 = {}
  PalletCreate({P8,P9,P10,P11},{4,6},points_Output1_24)
  local points_Output25_30 = {}
  PalletCreate({P20,P21},{3},points_Output25_30)
  local points_Output31_36 = {}
  PalletCreate({P22,P23},{3},points_Output31_36)
MoveReadIO(movemode.movj, P7)
if b<25 then
  for count = 1, 4 do
	MoveReadIO(movemode.movl, RelPoint(points_Output1_24[b], {0, 0, (k-2)*Caotray_output, 0}))
    Sync()
	DO((b-1) % 4 + 4, 0)
    b = b + 1
	OK = OK + 1
    Sleep(50)
  end
else
  Sync()
  for count2 = 1, 2 do
    if (b%2)==1 then
	  MoveReadIO(movemode.movl, RelPoint(points_Output25_30[b2], {0, 0, (k-2)*Caotray_output, 0}))
      DO(4,0)
	  Sync()
	  MoveReadIO(movemode.relmovl, {P24.coordinate[1] - P20.coordinate[1], P24.coordinate[2] - P20.coordinate[2], 0, P24.coordinate[4] - P20.coordinate[4]})
      DO(5,0)
    end
    if (b%2)==0 then
	  MoveReadIO(movemode.movl, RelPoint(points_Output31_36[b2], {0, 0, (k-2)*Caotray_output, 0}))
      DO(6,0)
	  Sync()
	  MoveReadIO(movemode.relmovl, {P24.coordinate[1] - P20.coordinate[1], P24.coordinate[2] - P20.coordinate[2], 0, P24.coordinate[4] - P20.coordinate[4]})
      DO(7,0)
    end
    b = b + 1
	OK = OK + 1
    Sleep(50)
  end
  b2 = b2 + 1
end
MoveReadIO(movemode.movj, P7)
Sync()
end

function Thay_input()
MoveReadIO(movemode.movj, P12)
MoveReadIO(movemode.movl, RelPoint(P13, {0, 0, (1-i)*Caotray_input, 0}))
Vaccumon( )
DO(9,1)
Wait( math.ceil(0.5 * 1000) )
MoveReadIO(movemode.movl, P12, {SpeedL = 11})
MoveReadIO(movemode.movj, P14, {SpeedJ = 20})
MoveReadIO(movemode.movl, RelPoint(P15, {0, 0, (i-1)*Caotray_input, 0}))
Vaccumoff( )
DO(9,0)
Wait( math.ceil(0.2 * 1000) )
MoveReadIO(movemode.movl, P14, {CP = 100})
i = i + 1
Sync()
end

function Thay_output()
MoveReadIO(movemode.movj, P16, {CP = 100})
MoveReadIO(movemode.movl, RelPoint(P17, {0, 0, (1-k)*Caotray_output, 0}))
Vaccumon( )
DO(9,1)
Wait( math.ceil(0.5 * 1000) )
MoveReadIO(movemode.movl, P16, {SpeedL = 10})
MoveReadIO(movemode.movj, P18, {SpeedJ = 20})
MoveReadIO(movemode.movl, RelPoint(P19, {0, 0, (k-1)*Caotray_output, 0}))
Vaccumoff( )
DO(9,0)
Move(P18)
k = k + 1
Sync()
end

function Vaccumoff()
Wait( math.ceil(0.2 * 1000) )
DO(4,0)
DO(5,0)
DO(6,0)
DO(7,0)
Wait( math.ceil(0.2 * 1000) )
end

function Vaccumon()
Wait( math.ceil(0.2 * 1000) )
DO(4,1)
DO(5,1)
DO(6,1)
DO(7,1)
Wait( math.ceil(0.2 * 1000) )
end
