Caotray_output = 6.8
Caotray_input = 7.2
SpeedJ(90)
SpeedL(90)
AccJ(90)
AccL(90)
CP(100)
while true do
  pauseFlag = false
  resetFlag = false
  a = 1
  b = 1
  b2 = 1
  i = 1
  k = 1
  Go(P1)
  DO(1,1)
  DO(2,0)
  DO(3,0)
  Vaccumoff( )
  Sync()
  print(k)
  Thay_output( )
  Sync()
  while not (i==12) do
    Input( )
    Output( )
    Sync()
    if resetFlag then goto reset_point end
    if b>30 then
      b = 1
      b2 = 1
      Thay_output( )
    end
    Sync()
    if a>6 then
      a = 1
      Thay_input( )
    end
    Sleep(50)
  end
  Sync()
  while not (b==31) do
    Input( )
    Output( )
    if resetFlag then goto reset_point end
    Sleep(50)
  end
  Thay_input( )
  ::reset_point::
  Go(P1)
  pseudo_pause()
end