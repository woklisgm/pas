program Time; 
var 
    ts : System.TimeSpan; 
    stopWatch := new System.Diagnostics.Stopwatch; 
    i, n, a, count: integer; 
    x : boolean; 

begin 
  read(a); 
  count := 0;
  x := False; 
  // Засекаем
  stopWatch.Start; 
  for i := 2 to a do 
  begin 
    for n := 2 to i-1 do 
    begin 
      if i mod n = 0 then 
        x := True;
    end; 

    if x = False then
      count := count + 1
    else 
      x := False;
  end; 

  stopWatch.Stop; 
  if x then 
  writeln(i); 
  writeln('Count: ', count); 
  ts := stopWatch.Elapsed; 
  writelnFormat('Время работы: {0:00}:{1:00}:{2:00}.{3:000}',ts.Hours, ts.Minutes, ts.Seconds, ts.Milliseconds); 
end.
