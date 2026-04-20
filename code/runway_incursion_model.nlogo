;; =========================================================
;; RUNWAY INCURSION RISK SIMULATION
;; Authors: Caleb Stone, Jayden Yawkey, Brandon Badraoui
;; SP-490 Capstone — Spring 2026
;;
;; References:
;;   Johnson et al. (2016) — taxiway exit speeds by angle
;;   Stroeve et al. (2016) — A–E incursion severity categories
;;
;; Scale: 1 patch = 50 ft, 1 tick = 1 second
;; =========================================================

breed [ aircrafts aircraft ]
breed [ vehicles vehicle ]

globals [
  incursion-A-count
  incursion-B-count
  incursion-C-count
  incursion-D-count

  ft-per-patch
  next-ac-tick
  next-veh-tick
  encounter-log

  gate-x-list
  depot-x
  depot-y

  ;; Taxiway exit x-positions (set during draw)
  exit-x-list
  ;; Vehicle crossing x-positions
  crossing-x-list
]

aircrafts-own [
  speed
  decel-rate
  exit-speed
  on-runway?
  taxiing-to-gate?
  at-gate?
  taxiing-to-runway?
  departing?
  gate-x
  gate-timer
  my-exit-x           ;; which exit connector this plane targets
  uid
]

vehicles-own [
  uid
  phase
  my-cross-x          ;; which crossing point this vehicle uses
  target-y
]

patches-own [
  is-runway?
  is-taxiway?
  is-apron?
]

;; =========================================================
;; SETUP
;; =========================================================
to setup
  clear-all
  set ft-per-patch 50
  set incursion-A-count 0
  set incursion-B-count 0
  set incursion-C-count 0
  set incursion-D-count 0
  set next-ac-tick 3
  set next-veh-tick 15
  set encounter-log []

  set gate-x-list [ 12 16 20 24 28 ]
  set depot-x -25
  set depot-y -10

  ;; Exit positions and crossing positions set during draw
  set exit-x-list []
  set crossing-x-list []

  draw-airport
  reset-ticks
end

;; =========================================================
;; AIRPORT LAYOUT
;; =========================================================
to draw-airport
  ask patches [
    set pcolor 53
    set is-runway? false
    set is-taxiway? false
    set is-apron? false
  ]
  ask patches with [ abs pxcor < 40 and abs pycor < 22 ] [ set pcolor 54 ]

  ;; ======== RUNWAY 9/27 (Horizontal) ========
  ask patches with [ pycor >= -1 and pycor <= 1 and
                     pxcor >= min-pxcor + 3 and pxcor <= max-pxcor - 3 ] [
    set pcolor 2
    set is-runway? true
  ]
  ask patches with [ (pycor = 2 or pycor = -2) and
                     pxcor >= min-pxcor + 3 and pxcor <= max-pxcor - 3 ] [ set pcolor 9 ]
  ask patches with [ pycor = 0 and pxcor >= min-pxcor + 6 and pxcor <= max-pxcor - 6 ] [
    if (pxcor mod 4) < 2 [ set pcolor 9.9 ]
  ]
  ;; Thresholds
  ask patches with [ pycor >= -1 and pycor <= 1 and
                     pxcor >= min-pxcor + 3 and pxcor <= min-pxcor + 5 ] [ set pcolor 9.5 ]
  ask patches with [ pycor >= -1 and pycor <= 1 and
                     pxcor >= max-pxcor - 5 and pxcor <= max-pxcor - 3 ] [ set pcolor 9.5 ]

  ;; ======== RUNWAY 18/36 (Vertical) ========
  ask patches with [ pxcor >= -1 and pxcor <= 1 and
                     pycor >= min-pycor + 3 and pycor <= max-pycor - 3 ] [
    set pcolor 2
    set is-runway? true
  ]
  ask patches with [ (pxcor = 2 or pxcor = -2) and
                     pycor >= min-pycor + 3 and pycor <= max-pycor - 3 and
                     (pycor > 2 or pycor < -2) ] [ set pcolor 9 ]
  ask patches with [ pxcor = 0 and (pycor > 3 or pycor < -3) and
                     pycor >= min-pycor + 6 and pycor <= max-pycor - 6 ] [
    if (pycor mod 4) < 2 [ set pcolor 9.9 ]
  ]

  ;; ======== INTERSECTION ========
  ask patches with [ abs pxcor <= 2 and abs pycor <= 2 ] [
    set pcolor 1.5
    set is-runway? true
  ]

  ;; ======== PARALLEL TAXIWAY (Alpha) ========
  ask patches with [ pycor >= 6 and pycor <= 8 and pxcor >= -30 and pxcor <= 35 ] [
    set pcolor 4
    set is-taxiway? true
  ]
  ask patches with [ pycor = 7 and pxcor >= -30 and pxcor <= 35 ] [
    if (pxcor mod 3) < 2 [ set pcolor 44 ]
  ]

  ;; ======== ANGLED TAXIWAY EXITS — angle matches slider ========
  ;; Three exit connectors at different runway positions
  draw-angled-exit 8
  draw-angled-exit 18
  draw-angled-exit 28
  set exit-x-list [ 8 18 28 ]

  ;; Departure connector (straight, at x=-15)
  ask patches with [ pxcor >= -16 and pxcor <= -14 and pycor >= 2 and pycor <= 6 ] [
    set pcolor 4
    set is-taxiway? true
  ]
  ask patches with [ pxcor = -15 and pycor >= 2 and pycor <= 6 ] [ set pcolor 44 ]

  ;; ======== TERMINAL BUILDING ========
  ask patches with [ pxcor >= 10 and pxcor <= 30 and pycor >= 13 and pycor <= 17 ] [ set pcolor 7 ]
  ask patches with [ pxcor >= 10 and pxcor <= 30 and pycor = 17 ] [ set pcolor 8 ]

  ;; ======== APRON ========
  ask patches with [ pxcor >= 8 and pxcor <= 32 and pycor >= 8 and pycor <= 13 ] [
    set pcolor 3
    set is-apron? true
  ]
  foreach gate-x-list [ gx ->
    if gx >= min-pxcor and gx <= max-pxcor [
      ask patch gx 12 [ set pcolor 45 ]
      ask patch gx 11 [ set pcolor 45 ]
    ]
  ]

  ;; ======== VEHICLE DEPOT ========
  ask patches with [ pxcor >= -28 and pxcor <= -22 and pycor >= -13 and pycor <= -9 ] [ set pcolor 36 ]
  ask patches with [ pxcor >= -28 and pxcor <= -22 and pycor = -9 ] [ set pcolor 37 ]

  ;; ======== VEHICLE ROADS — multiple crossing points ========
  ;; Main service road (horizontal, below runway)
  ask patches with [ pycor = -7 and pxcor >= -22 and pxcor <= 30 ] [ set pcolor 3.5 ]

  ;; Crossing 1: x = -5 (near intersection)
  ask patches with [ pxcor = -5 and pycor >= -7 and pycor <= -2 ] [ set pcolor 3.5 ]
  ask patches with [ pxcor = -5 and pycor >= 2 and pycor <= 8 ] [ set pcolor 3.5 ]

  ;; Crossing 2: x = 9
  ask patches with [ pxcor = 9 and pycor >= -7 and pycor <= -2 ] [ set pcolor 3.5 ]
  ask patches with [ pxcor = 9 and pycor >= 2 and pycor <= 8 ] [ set pcolor 3.5 ]

  ;; Crossing 3: x = 22
  ask patches with [ pxcor = 22 and pycor >= -7 and pycor <= -2 ] [ set pcolor 3.5 ]
  ask patches with [ pxcor = 22 and pycor >= 2 and pycor <= 8 ] [ set pcolor 3.5 ]

  set crossing-x-list [ -5 9 22 ]

  ;; ======== CONTROL TOWER ========
  ask patches with [ pxcor >= -30 and pxcor <= -28 and pycor >= 10 and pycor <= 13 ] [ set pcolor 8 ]
  ask patch -29 13 [ set pcolor 9.5 ]
end

;; Draw an angled taxiway exit at given x-position
;; Angle follows the taxiway-exit-angle slider
to draw-angled-exit [ base-x ]
  let steps 5
  let angle-rad taxiway-exit-angle * (pi / 180)
  ;; dx per step: horizontal offset based on angle
  ;; At 45°, dx=1 per dy step. At 30°, dx=0.577 per step.
  let dx-per-step tan (90 - taxiway-exit-angle)
  let i 0
  while [ i < steps ] [
    let ey 2 + i   ;; y goes from runway edge (2) upward
    let ex round (base-x + i * dx-per-step)
    if ex >= min-pxcor and ex <= max-pxcor and ey >= min-pycor and ey <= max-pycor [
      ask patch ex ey [
        set pcolor 4
        set is-taxiway? true
      ]
      ;; Make it 2 patches wide
      if (ex + 1) <= max-pxcor [
        ask patch (ex + 1) ey [
          set pcolor 4
          set is-taxiway? true
        ]
      ]
      ;; Yellow center guide
      ask patch ex ey [ set pcolor 44 ]
    ]
    set i i + 1
  ]
end

;; =========================================================
;; MAIN LOOP
;; =========================================================
to go
  ;; --- Aircraft spawn (timed, capped at 6 total) ---
  if ticks >= next-ac-tick [
    if count aircrafts < 6 [
      spawn-landing-aircraft
    ]
    let jitter spawn-interval * 0.3
    set next-ac-tick ticks + spawn-interval + random-float (jitter * 2) - jitter
  ]

  ;; --- Vehicle spawn (timed, capped at 4 total) ---
  ;; Vehicles CAN cross while aircraft are on runway — that's how incursions happen!
  if ticks >= next-veh-tick [
    if count vehicles < 4 [
      spawn-vehicle-from-depot
    ]
    let interval max list 15 (2500 / (max list 1 vehicle-crossing-frequency))
    set next-veh-tick ticks + interval + random 10 - 5
  ]

  ;; --- Gate departures (only if runway clear of landing aircraft) ---
  ask aircrafts with [ at-gate? and gate-timer > 0 ] [
    set gate-timer gate-timer - 1
    if gate-timer <= 0 [
      if not any? other aircrafts with [ on-runway? and not departing? ] [
        begin-departure
      ]
    ]
  ]

  ask aircrafts [ move-aircraft ]
  ask vehicles  [ move-vehicle ]
  calculate-incursions
  cleanup

  tick
end

;; =========================================================
;; SPAWN: Landing aircraft
;; =========================================================
to spawn-landing-aircraft
  create-aircrafts 1 [
    setxy (min-pxcor + 4) 0
    set heading 90
    set color white
    set shape "airplane"
    set size 3

    set speed (150 * 1.467 / ft-per-patch)

    ifelse taxiway-exit-angle = 45
      [ set exit-speed (40 * 1.467 / ft-per-patch) ]
      [ set exit-speed (60 * 1.467 / ft-per-patch) ]

    let base (0.3 * 32.174 / ft-per-patch)
    set decel-rate base * (1 + wind-modifier / 100) * (0.85 + random-float 0.3)

    set on-runway? true
    set taxiing-to-gate? false
    set at-gate? false
    set taxiing-to-runway? false
    set departing? false
    set gate-x one-of gate-x-list
    ;; Pick a random exit connector
    set my-exit-x one-of exit-x-list
    set gate-timer 0
    set uid (word "A" ticks)
  ]
end

;; =========================================================
;; Begin departure
;; =========================================================
to begin-departure
  set at-gate? false
  set taxiing-to-runway? true
  set color cyan
  set heading 180
end

;; =========================================================
;; AIRCRAFT MOVEMENT
;; =========================================================
to move-aircraft
  ;; === PHASE 1: Landing roll ===
  if on-runway? and not departing? [
    if speed > 0.05 [
      set speed speed - decel-rate
      if speed < 0 [ set speed 0 ]
    ]
    if speed <= 0.05 [ set speed 0.15 ]

    fd speed

    ;; Exit when slow enough AND near assigned exit
    if speed <= (exit-speed + 0.1) [
      if abs (xcor - my-exit-x) < 3 and ycor <= 2 [
        set on-runway? false
        set taxiing-to-gate? true
        set color 65
        set speed 0
        ;; Head in the direction of the angled taxiway
        set heading (90 - taxiway-exit-angle)
      ]
    ]

    ;; Force exit at runway end
    if xcor >= (max-pxcor - 5) [
      set on-runway? false
      set taxiing-to-gate? true
      set color 65
      set speed 0
      set heading 0
    ]
    stop
  ]

  ;; === PHASE 2: Taxi to gate ===
  if taxiing-to-gate? [
    if ycor < 7 [
      set heading 0
      fd 0.35
      stop
    ]
    if ycor >= 7 and ycor < 11 [
      ifelse abs (xcor - gate-x) > 1 [
        ifelse xcor < gate-x [ set heading 90 ] [ set heading 270 ]
        fd 0.35
      ] [
        set heading 0
        fd 0.35
      ]
      stop
    ]
    if ycor >= 11 [
      set taxiing-to-gate? false
      set at-gate? true
      set color blue
      set gate-timer (30 + random 50)
      setxy gate-x 12
    ]
    stop
  ]

  ;; === PHASE 3: Taxi to runway for departure ===
  if taxiing-to-runway? [
    if ycor > 7 [
      set heading 180
      fd 0.35
      stop
    ]
    if ycor >= 6 and ycor <= 8 [
      ifelse xcor > -14 [
        set heading 270
        fd 0.35
      ] [
        set heading 180
        fd 0.35
        if ycor <= 1 [
          set taxiing-to-runway? false
          set departing? true
          set heading 90
          set speed 0.1
          set on-runway? true
          set color yellow
        ]
      ]
      stop
    ]
    set heading 180
    fd 0.35
    if ycor <= 1 [
      set taxiing-to-runway? false
      set departing? true
      set heading 90
      set speed 0.1
      set on-runway? true
      set color yellow
    ]
    stop
  ]

  ;; === PHASE 4: Departure takeoff roll ===
  if departing? [
    set speed speed + decel-rate * 0.5
    fd speed
    if xcor >= (max-pxcor - 5) [ die ]
    stop
  ]
end

;; =========================================================
;; SPAWN: Vehicle from depot
;; =========================================================
to spawn-vehicle-from-depot
  create-vehicles 1 [
    setxy depot-x (depot-y + 3)
    set heading 90
    set color orange
    set shape "car"
    set size 2
    set phase "to-runway"
    ;; Pick a random crossing point
    set my-cross-x one-of crossing-x-list
    set target-y 8
    set uid (word "V" ticks)
  ]
end

;; =========================================================
;; VEHICLE MOVEMENT — uses assigned crossing point
;; =========================================================
to move-vehicle
  ;; === Drive east along service road to assigned crossing ===
  if phase = "to-runway" [
    if ycor < -6.5 [
      set heading 0
      fd 0.4
      stop
    ]
    ifelse xcor < (my-cross-x - 1) [
      set heading 90
      fd 0.5
    ] [
      set phase "crossing"
      set heading 0
    ]
    stop
  ]

  ;; === Cross the runway (DANGER ZONE) ===
  if phase = "crossing" [
    fd 0.4
    if ycor > 5 [
      set phase "to-terminal"
      set heading 0
    ]
    stop
  ]

  ;; === Continue to terminal ===
  if phase = "to-terminal" [
    fd 0.35
    if ycor >= target-y [
      set phase "at-terminal"
      set color green
    ]
    stop
  ]

  ;; === At terminal, then return ===
  if phase = "at-terminal" [
    set phase "returning"
    set heading 180
    set color orange
    stop
  ]

  ;; === Return south across runway back to depot ===
  if phase = "returning" [
    fd 0.45
    if ycor < -6 [ set heading 270 ]
    if xcor <= (depot-x + 5) [ die ]
    if ycor <= min-pycor + 2 [ die ]
    if xcor <= min-pxcor + 2 [ die ]
    stop
  ]
end

;; =========================================================
;; INCURSION DETECTION — Stroeve et al. (2016)
;;
;; Cat A happens when agents are < 1 patch apart (< 50 ft).
;; This requires a vehicle crossing while an aircraft is
;; rolling through the same area — which now CAN happen
;; since we removed the "don't spawn if runway occupied" guard.
;; =========================================================
to calculate-incursions
  let active-ac aircrafts with [ on-runway? ]
  ;; Vehicles in or near the runway zone
  let danger-veh vehicles with [ (phase = "crossing" or phase = "returning") and
                                  ycor > -3 and ycor < 3 ]

  ;; Aircraft ↔ Vehicle
  ask active-ac [
    let me self
    let my-uid uid
    ask danger-veh [
      let pair-id (word my-uid uid)
      if not member? pair-id encounter-log [
        let sep (distance me) * ft-per-patch
        if sep < 500 [
          if sep < 50  [ set incursion-A-count incursion-A-count + 1 ]
          if sep >= 50  and sep < 100 [ set incursion-B-count incursion-B-count + 1 ]
          if sep >= 100 and sep < 200 [ set incursion-C-count incursion-C-count + 1 ]
          if sep >= 200 and sep < 500 [ set incursion-D-count incursion-D-count + 1 ]
          set encounter-log lput pair-id encounter-log
        ]
      ]
    ]
  ]

  ;; Aircraft ↔ Aircraft
  if count active-ac >= 2 [
    let acs sort active-ac
    let i 0
    while [ i < length acs - 1 ] [
      let j i + 1
      while [ j < length acs ] [
        let a1 item i acs
        let a2 item j acs
        let pair-id (word [uid] of a1 [uid] of a2)
        if not member? pair-id encounter-log [
          let sep ([distance a2] of a1) * ft-per-patch
          if sep < 500 [
            if sep < 50  [ set incursion-A-count incursion-A-count + 1 ]
            if sep >= 50  and sep < 100 [ set incursion-B-count incursion-B-count + 1 ]
            if sep >= 100 and sep < 200 [ set incursion-C-count incursion-C-count + 1 ]
            if sep >= 200 and sep < 500 [ set incursion-D-count incursion-D-count + 1 ]
            set encounter-log lput pair-id encounter-log
          ]
        ]
        set j j + 1
      ]
      set i i + 1
    ]
  ]

  if length encounter-log > 300 [
    set encounter-log sublist encounter-log (length encounter-log - 100) (length encounter-log)
  ]
end

;; =========================================================
;; CLEANUP
;; =========================================================
to cleanup
  ask turtles [
    if xcor >= max-pxcor - 1 or xcor <= min-pxcor + 1 or
       ycor >= max-pycor - 1 or ycor <= min-pycor + 1 [
      if not at-gate? [ die ]
    ]
  ]
end
