# Defrost profile: 3× 60s at 30/40/50 with beeps
stage "Defrost 30%" {
  power 30
  cook 60
  beep
}
stage "Defrost 40%" {
  power 40
  cook 60
  beep
}
stage "Defrost 50%" {
  power 50
  cook 60
  beep
}
halt