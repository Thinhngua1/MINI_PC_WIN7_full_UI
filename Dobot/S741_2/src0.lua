SpeedJ(100)
SpeedL(100)
AccJ(50)
AccL(50)
CP(100)
Caotray_output = 6.5
Caotray_input = 7.7
while true do
  a = 1
  b = 1
  i = 0
  k = 0
  pauseFlag = false
  resetFlag = false
  MovJ(P1)
  DOGroup({4,0},{5,0},{6,0},{7,0},{8,0},{9,0})
  Thay_output( )
  Sync()
  while not (i==4) do
    Input( )
    Output( )
    Sync()
    if resetFlag then goto reset_point end
    if b>30 then
      b = 1
      Thay_output( )
    end
    Sync()
    if a>8 then
      a = 1
      Thay_input( )
    end
    Sleep(50)
  end
  Sync()
  while not (a==9) do
    Input( )
    Output( )
    if resetFlag then goto reset_point end
    Sleep(50)
  end
  Thay_input( )
  ::reset_point::
  MovJ(P1)
  pseudo_pause()
end