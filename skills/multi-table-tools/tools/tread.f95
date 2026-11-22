program tread
  implicit none
  character(len=256) :: fname
  character(len=15)  :: a2
  real*8             :: a1,a3,a4
  integer            :: u=3, ios
  call get_command_argument(1,fname)
  open(u,file=trim(fname),status='old',form='formatted')
  read(u,'(e15.0,a,2e15.8)',iostat=ios) a1,a2,a3,a4
  if(ios/=0)then
     print *,'HEADER READ FAIL'
     stop 1
  endif
  print '(a,i8,a,a,a,i5,a,i5)','id=',int(a1),' type=[',a2,'] nr=',int(a3),' nt=',int(a4)
  close(u)
end program tread
