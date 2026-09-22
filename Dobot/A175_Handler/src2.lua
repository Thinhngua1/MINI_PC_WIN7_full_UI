-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5
while true do
  if DI(3) == 1 then pauseFlag = true end -- nút Pause
  if DI(5) == 1 then resetFlag = true end -- nút Reset
  if pauseFlag or resetFlag then DOGroup({1, 0}, {3, 1})
  else DOGroup({1, 1}, {3, 0}) end
  Sleep(50)
end