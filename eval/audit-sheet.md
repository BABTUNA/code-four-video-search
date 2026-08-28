# Truth-span audit sheet

Jump to each timestamp, watch about twenty seconds, and keep the
box only if the event is really there. Strike the rest.

## "officer reads someone their rights"  (direct)
- [ ] **video_13 9:28-9:53** · "You have the right to remain silent"
- [ ] **video_19 7:15-7:35** · "And you can either hire an attorney or come back and talk to the judge"
- [ ] **video_20 19:06-19:28** · "You can get an attorney, you can go through court, you can do everythi"
- [ ] **video_38 18:24-18:42** · "You have the right to remain silent."

Truth YAML for kept boxes:
```yaml
  - query: officer reads someone their rights
    type: direct
    truth:
      - {video: video_13, start: 569, end: 593}
      - {video: video_19, start: 435, end: 455}
      - {video: video_20, start: 1147, end: 1168}
      - {video: video_38, start: 1105, end: 1122}
```

## "officer orders the driver to step out of the vehicle"  (direct)
- [ ] **video_16 2:52-3:10** · "Alright, Ms. Diaz, I need you to step out the car."
- [ ] **video_16 4:35-4:58** · "Can you step out for me real quick, my man?"
- [ ] **video_18 2:54-3:13** · "How about if I step outside and I'll wait for your sergeant to get her"
- [ ] **video_19 1:28-1:45** · "Do you want me to go out of the car?"
- [ ] **video_29 0:00-0:18** · "Are you able to step out with me?"
- [ ] **video_29 2:46-3:20** · "Chase, so the reason why we pulled you out of the car..."
- [ ] **video_29 5:34-5:53** · "Is there anything out of the car that you need your wallet? Anything l"
- [ ] **video_38 2:01-2:22** · "is that you step out of the vehicle we'll do some exercises and we'll "

Truth YAML for kept boxes:
```yaml
  - query: officer orders the driver to step out of the vehicle
    type: direct
    truth:
      - {video: video_16, start: 172, end: 190}
      - {video: video_16, start: 276, end: 298}
      - {video: video_18, start: 174, end: 194}
      - {video: video_19, start: 88, end: 105}
      - {video: video_29, start: 1, end: 18}
      - {video: video_29, start: 166, end: 200}
      - {video: video_29, start: 335, end: 353}
      - {video: video_38, start: 122, end: 143}
```

## "a person is being handcuffed"  (cross_modal)
- [ ] **video_13 0:25-2:37** · "An officer engages with a young man in a patterned shirt, placing him "
- [ ] **video_13 9:52-10:08** · "An officer checks on a handcuffed person sitting in the rear of a poli"
- [ ] **video_13 21:37-23:44** · "An officer opening the rear door of a police SUV where a handcuffed in"
- [ ] **video_13 27:25-27:43** · "I'll let you go without handcuffs in the car."
- [ ] **video_16 2:52-5:08** · "The female driver is instructed to exit the vehicle and is handcuffed "
- [ ] **video_16 14:52-16:23** · "An adult female with long dark hair, wearing a green hoodie and sweatp"
- [ ] **video_18 2:24-2:42** · "to get you in handcuffs and arrested."
- [ ] **video_19 0:34-1:13** · "The officer directs the driver to face the vehicle and places him in c"
- [ ] **video_20 4:49-5:08** · "Officer instructs the female driver to place her hands behind her back"
- [ ] **video_20 13:34-18:49** · "The officer places the woman in handcuffs and informs her she is under"
- [ ] **video_22 3:44-4:02** · "Just put your hands behind your back right there."
- [ ] **video_24 3:04-3:38** · "An officer in uniform applies handcuffs to a shirtless individual wear"
- [ ] **video_24 5:51-7:12** · "The officer stops behind a golf cart and another police SUV, speaking "
- [ ] **video_24 16:42-20:08** · "The shirtless man stands near a marked Las Cruces Police Department SU"
- [ ] **video_28 0:19-2:11** · "Law enforcement officer places handcuffs on the woman near the pool ar"
- [ ] **video_28 4:25-5:57** · "Officers interact with a woman near the pool area and secure her in ha"
- [ ] **video_28 6:22-8:50** · "Officers escort the handcuffed person along the pool patio area."
- [ ] **video_28 10:21-13:26** · "An officer in uniform escorts a handcuffed individual in dark clothing"
- [ ] **video_35 0:22-3:18** · "Officer catches up to the fleeing person on rough terrain, takes him t"
- [ ] **video_35 4:52-5:53** · "An officer talks to a handcuffed adult male wearing a white t-shirt an"
- [ ] **video_35 10:42-12:16** · "Officer escorts a handcuffed male subject wearing a white t-shirt and "
- [ ] **video_36 13:54-15:08** · "Law enforcement officers approach the individual on the ground, take t"
- [ ] **video_36 23:52-24:09** · "Body-worn camera view shows the detained person seated in the back of "
- [ ] **video_38 20:59-22:58** · "An officer places a person in handcuffs."
- [ ] **video_38 23:57-24:58** · "An officer places the handcuffed individual into the rear of a police "
- [ ] **video_4 4:52-5:08** · "Handcuffing takes place as officers place the man in handcuffs behind "
- [ ] **video_4 11:22-15:08** · "Officers discussing handcuff adjustment and phone removal for a person"
- [ ] **video_4 20:07-20:38** · "A detained person in a grey graphic t-shirt standing with hands cuffed"
- [ ] **video_4 24:35-24:54** · "I was in handcuffs when I gave it to you"

Truth YAML for kept boxes:
```yaml
  - query: a person is being handcuffed
    type: cross_modal
    truth:
      - {video: video_13, start: 25, end: 157}
      - {video: video_13, start: 592, end: 608}
      - {video: video_13, start: 1297, end: 1424}
      - {video: video_13, start: 1646, end: 1663}
      - {video: video_16, start: 172, end: 308}
      - {video: video_16, start: 892, end: 983}
      - {video: video_18, start: 145, end: 162}
      - {video: video_19, start: 34, end: 73}
      - {video: video_20, start: 289, end: 308}
      - {video: video_20, start: 814, end: 1129}
      - {video: video_22, start: 225, end: 242}
      - {video: video_24, start: 184, end: 218}
      - {video: video_24, start: 351, end: 432}
      - {video: video_24, start: 1002, end: 1208}
      - {video: video_28, start: 19, end: 131}
      - {video: video_28, start: 265, end: 357}
      - {video: video_28, start: 382, end: 530}
      - {video: video_28, start: 621, end: 806}
      - {video: video_35, start: 22, end: 198}
      - {video: video_35, start: 292, end: 353}
      - {video: video_35, start: 642, end: 736}
      - {video: video_36, start: 834, end: 908}
      - {video: video_36, start: 1432, end: 1449}
      - {video: video_38, start: 1259, end: 1378}
      - {video: video_38, start: 1437, end: 1498}
      - {video: video_4, start: 292, end: 308}
      - {video: video_4, start: 682, end: 908}
      - {video: video_4, start: 1207, end: 1238}
      - {video: video_4, start: 1476, end: 1494}
```

## "a vehicle stopped by police at night"  (cross_modal)
- [ ] **video_16 0:00-0:14** · "An officer driving a police vehicle during a traffic stop, approaching"
- [ ] **video_16 4:52-5:23** · "A man in a black t-shirt with text standing outside a blue car during "
- [ ] **video_19 0:00-0:50** · "An officer conducts a traffic stop on a highway in bright daylight, in"
- [ ] **video_19 9:52-10:26** · "An officer stands near a white sports car on the shoulder of a highway"
- [ ] **video_20 0:00-0:26** · "Officer sitting inside the patrol vehicle at night during a traffic st"
- [ ] **video_20 4:52-5:22** · "An officer gives instructions to a woman wearing a white dress and boo"
- [ ] **video_20 9:52-10:08** · "A police vehicle with flashing emergency lights is visible parked behi"
- [ ] **video_20 19:52-20:34** · "An officer talks with a woman wearing a red jersey on the side of a ro"
- [ ] **video_20 23:42-25:18** · "Two officers converse about the details of the traffic stop and the dr"
- [ ] **video_29 0:00-0:21** · "An officer interacts with a driver seated inside a pickup truck during"
- [ ] **video_38 18:30-20:08** · "The officer administers Miranda warnings to the woman and questions he"

Truth YAML for kept boxes:
```yaml
  - query: a vehicle stopped by police at night
    type: cross_modal
    truth:
      - {video: video_16, start: 0, end: 14}
      - {video: video_16, start: 292, end: 323}
      - {video: video_19, start: 0, end: 50}
      - {video: video_19, start: 592, end: 626}
      - {video: video_20, start: 0, end: 26}
      - {video: video_20, start: 292, end: 322}
      - {video: video_20, start: 592, end: 608}
      - {video: video_20, start: 1192, end: 1234}
      - {video: video_20, start: 1422, end: 1518}
      - {video: video_29, start: 0, end: 21}
      - {video: video_38, start: 1110, end: 1208}
```

## "someone raises their voice"  (cross_modal)
- [ ] **video_12 8:04-9:48** · "Officers and a firefighter in a yellow vest converse on the paved lot "
- [ ] **video_27 25:10-25:35** · "Dashcam view as a yellow pickup truck passes by on the highway."
- [ ] **video_28 15:22-17:04** · "A man in a yellow shirt writes on a notepad resting on the hood of a b"
- [ ] **video_9 9:42-10:08** · "The officer holds a stack of yellow legal pads with handwritten notes,"

Truth YAML for kept boxes:
```yaml
  - query: someone raises their voice
    type: cross_modal
    truth:
      - {video: video_12, start: 484, end: 588}
      - {video: video_27, start: 1510, end: 1535}
      - {video: video_28, start: 922, end: 1024}
      - {video: video_9, start: 582, end: 608}
```

## "a field sobriety test is conducted"  (cross_modal)
- [ ] **video_20 4:02-7:53** · "Officer conducts a horizontal gaze nystagmus field sobriety test with "
- [ ] **video_20 9:52-13:50** · "An officer administers a field sobriety test to a woman wearing a whit"
- [ ] **video_29 3:06-3:24** · "Would you be willing to do some sobriety exercises for us tonight?"
- [ ] **video_29 4:29-5:06** · "We do the field sobriety exercises."
- [ ] **video_38 3:47-5:22** · "Driver stands outside vehicle and interacts with officer while prepari"
- [ ] **video_38 5:39-7:08** · "The woman stands facing the camera while listening to instructions dur"
- [ ] **video_38 8:27-10:57** · "The officer explains and demonstrates the walking and turning portion "
- [ ] **video_38 12:50-15:20** · "The woman attempts the one-leg stand field sobriety test in the parkin"
- [ ] **video_38 15:38-16:11** · "The officer gives further instructions for the field sobriety test whi"
- [ ] **video_4 19:37-19:53** · "Put one leg in."

Truth YAML for kept boxes:
```yaml
  - query: a field sobriety test is conducted
    type: cross_modal
    truth:
      - {video: video_20, start: 242, end: 473}
      - {video: video_20, start: 592, end: 830}
      - {video: video_29, start: 186, end: 205}
      - {video: video_29, start: 270, end: 306}
      - {video: video_38, start: 227, end: 322}
      - {video: video_38, start: 339, end: 428}
      - {video: video_38, start: 507, end: 657}
      - {video: video_38, start: 770, end: 920}
      - {video: video_38, start: 938, end: 971}
      - {video: video_4, start: 1177, end: 1194}
```

## "officers pursue someone on foot"  (cross_modal)
- [ ] **video_10 12:12-12:41** · "My personal belongings, clothes, shoes, a TV that I purchased."
- [ ] **video_13 0:54-1:15** · "Get on the ground."
- [ ] **video_28 9:26-9:46** · "My shoes, I was running from this side because he put his hands on me."
- [ ] **video_29 1:31-2:23** · "Chase Mina."
- [ ] **video_29 2:44-3:04** · "It's Chase, right?"
- [ ] **video_29 4:23-4:40** · "Okay, Chase."
- [ ] **video_29 12:49-13:22** · "Was it Chase?"
- [ ] **video_35 0:00-0:38** · "Officer engages in a foot pursuit of a fleeing person wearing a white "
- [ ] **video_35 3:16-3:34** · "I need to try to attend another foot pursuit of black."
- [ ] **video_35 16:39-16:56** · "I just chased after that guy."
- [ ] **video_35 17:49-18:08** · "There's another gentleman that took off after I chased after him, and."
- [ ] **video_35 21:58-22:17** · "The whole reason I chased him is because I thought he was your guy."
- [ ] **video_36 1:11-1:29** · "I've got a white Dodge Starker running from me."
- [ ] **video_36 2:35-2:54** · "White Farger's running from J-21."
- [ ] **video_39 12:17-12:48** · "The high-speed chase continues along the interstate with sparse traffi"

Truth YAML for kept boxes:
```yaml
  - query: officers pursue someone on foot
    type: cross_modal
    truth:
      - {video: video_10, start: 733, end: 762}
      - {video: video_13, start: 55, end: 75}
      - {video: video_28, start: 566, end: 586}
      - {video: video_29, start: 92, end: 143}
      - {video: video_29, start: 164, end: 185}
      - {video: video_29, start: 264, end: 280}
      - {video: video_29, start: 769, end: 803}
      - {video: video_35, start: 0, end: 38}
      - {video: video_35, start: 196, end: 214}
      - {video: video_35, start: 1000, end: 1016}
      - {video: video_35, start: 1069, end: 1089}
      - {video: video_35, start: 1318, end: 1337}
      - {video: video_36, start: 71, end: 89}
      - {video: video_36, start: 156, end: 174}
      - {video: video_39, start: 737, end: 768}
```

## "an ambulance or medics are called to the scene"  (direct)
- [ ] **video_10 22:03-22:19** · "The man exits the apartment carrying items and walks down the hallway."
- [ ] **video_11 1:20-1:37** · "The medicine right here."
- [ ] **video_11 3:21-5:08** · "Just get me in an ambulance."
- [ ] **video_11 5:42-7:20** · "Officers and emergency workers coordinate logistics regarding animals "
- [ ] **video_11 9:52-10:08** · "Firefighters and emergency medical personnel administer aid and manage"
- [ ] **video_11 14:42-15:22** · "Officers conversing while medical stretcher and emergency personnel ar"
- [ ] **video_11 16:03-18:26** · "Multiple officers converse about medical transport procedures at night"
- [ ] **video_12 1:36-1:53** · "Stop, the medic team's right here!"
- [ ] **video_12 4:52-5:08** · "Officers and firefighters gather near medical equipment and injured in"
- [ ] **video_12 10:17-10:54** · "Firefighter interacting with dogs inside the back of a truck or ambula"
- [ ] **video_12 11:43-14:20** · "AMR ambulances parked in the lot with emergency lights flashing at nig"
- [ ] **video_13 6:37-7:58** · "An officer uses a flashlight to inspect items on the passenger seat of"
- [ ] **video_13 19:54-20:37** · "Do you need any medical attention?"
- [ ] **video_13 21:23-21:41** · "He needs a dispatcher medics, just PPD holding."
- [ ] **video_13 26:08-27:52** · "Two emergency medical personnel enter the room to evaluate the man in "
- [ ] **video_16 16:07-17:03** · "The woman is seated on a bench in the holding area, talking while a me"
- [ ] **video_20 8:06-8:23** · "Do you have any knee and ankle hip problems?"
- [ ] **video_20 21:43-23:26** · "The officer shines a flashlight inside the vehicle and gathers persona"
- [ ] **video_20 25:08-26:12** · "Close-up view of items on the front passenger seat including plastic b"
- [ ] **video_22 1:12-1:29** · "Did you have problems with him, too?"
- [ ] **video_22 1:57-2:13** · "It seems okay."
- [ ] **video_22 3:24-5:08** · "An officer frisking the seated man and speaking about items in his pos"
- [ ] **video_22 7:24-7:48** · "He's causing problems."
- [ ] **video_27 5:28-5:48** · "We're in contact next ambulance, please."
- [ ] **video_27 8:22-8:40** · "She seems to be okay."
- [ ] **video_27 9:15-9:34** · "I was going to advise you EMS Breast Care 10-19."
- [ ] **video_27 10:29-10:47** · "We got ambulance on the way."
- [ ] **video_27 13:44-14:03** · "I was waiting on the ambulance and then to come check her out."
- [ ] **video_27 17:56-18:16** · "She told the, this interview guy said he's a medic."
- [ ] **video_28 9:03-9:20** · "We don't want no problems with her."
- [ ] **video_29 2:19-3:50** · "The driver leans back into the truck to retrieve personal items before"
- [ ] **video_29 4:26-4:45** · "So generally what we do is we're running through some medical question"
- [ ] **video_35 4:22-5:08** · "Officer places items recovered from the detainee onto the hood of a po"
- [ ] **video_35 6:40-7:40** · "The officer stands near the front of a dark police SUV and organizes v"
- [ ] **video_35 12:02-12:20** · "Apparently she bagged items without scanning them either."
- [ ] **video_35 12:38-12:57** · "She scan items or didn't scan items?"
- [ ] **video_36 18:52-19:38** · "Officers inspect items retrieved from the vehicle."
- [ ] **video_36 20:06-20:30** · "An officer standing near the rear of the white car disposes of items f"
- [ ] **video_4 8:55-9:16** · "He is medically not on shift."
- [ ] **video_4 17:26-17:44** · "We're not going to do problems inside of the road."
- [ ] **video_4 20:34-21:20** · "An officer handling evidence bags and inspecting personal items near t"
- [ ] **video_9 11:18-11:36** · "And they're trying to make a list for her themselves."

Truth YAML for kept boxes:
```yaml
  - query: an ambulance or medics are called to the scene
    type: direct
    truth:
      - {video: video_10, start: 1323, end: 1339}
      - {video: video_11, start: 81, end: 97}
      - {video: video_11, start: 201, end: 308}
      - {video: video_11, start: 342, end: 440}
      - {video: video_11, start: 592, end: 608}
      - {video: video_11, start: 882, end: 922}
      - {video: video_11, start: 963, end: 1106}
      - {video: video_12, start: 97, end: 114}
      - {video: video_12, start: 292, end: 308}
      - {video: video_12, start: 617, end: 654}
      - {video: video_12, start: 703, end: 860}
      - {video: video_13, start: 397, end: 478}
      - {video: video_13, start: 1195, end: 1238}
      - {video: video_13, start: 1283, end: 1301}
      - {video: video_13, start: 1568, end: 1672}
      - {video: video_16, start: 967, end: 1023}
      - {video: video_20, start: 486, end: 503}
      - {video: video_20, start: 1303, end: 1406}
      - {video: video_20, start: 1508, end: 1572}
      - {video: video_22, start: 72, end: 89}
      - {video: video_22, start: 117, end: 134}
      - {video: video_22, start: 204, end: 308}
      - {video: video_22, start: 444, end: 468}
      - {video: video_27, start: 329, end: 348}
      - {video: video_27, start: 503, end: 520}
      - {video: video_27, start: 556, end: 575}
      - {video: video_27, start: 629, end: 647}
      - {video: video_27, start: 824, end: 844}
      - {video: video_27, start: 1077, end: 1096}
      - {video: video_28, start: 543, end: 560}
      - {video: video_29, start: 139, end: 230}
      - {video: video_29, start: 267, end: 285}
      - {video: video_35, start: 262, end: 308}
      - {video: video_35, start: 400, end: 460}
      - {video: video_35, start: 722, end: 741}
      - {video: video_35, start: 759, end: 777}
      - {video: video_36, start: 1132, end: 1178}
      - {video: video_36, start: 1206, end: 1230}
      - {video: video_4, start: 536, end: 556}
      - {video: video_4, start: 1047, end: 1065}
      - {video: video_4, start: 1234, end: 1280}
      - {video: video_9, start: 678, end: 696}
```

## "a vehicle is towed or impounded"  (direct)
- [ ] **video_10 0:20-1:04** · "No, she used to, she's been out for about a month, but she's just in t"
- [ ] **video_10 8:45-10:52** · "The officers park their bicycles inside the lobby and walk through the"
- [ ] **video_10 11:17-11:35** · "Okay, have you ever contributed any money towards rent?"
- [ ] **video_10 20:14-20:37** · "The man walks down the hallway towards two police officers standing ou"
- [ ] **video_10 22:03-22:19** · "The man walks back down the hallway toward the elevators accompanied b"
- [ ] **video_11 0:00-0:55** · "Officer approaches the scene outdoors at night near parked semi-trucks"
- [ ] **video_11 13:46-14:10** · "It was towards the back."
- [ ] **video_11 16:42-17:38** · "An officer walks toward an AMR ambulance and approaches the rear doors"
- [ ] **video_12 0:06-1:03** · "Officer runs towards a truck fire with an attached horse trailer, enco"
- [ ] **video_12 8:25-8:42** · "Nah, we'll get it towed in place."
- [ ] **video_12 10:04-10:33** · "Camera view moving toward the back of an emergency vehicle with multip"
- [ ] **video_13 14:02-15:08** · "in town too."
- [ ] **video_16 0:00-0:42** · "View of the blue Chevrolet sedan from behind and the driver side, with"
- [ ] **video_16 5:50-6:08** · "I won't tow the vehicle on anything right now, okay?"
- [ ] **video_16 7:45-8:02** · "Cause like today, it could've got tow"
- [ ] **video_16 9:39-9:57** · "I'll tow this thing"
- [ ] **video_18 0:03-0:38** · "Officer enters the library and walks through the interior toward the c"
- [ ] **video_18 4:52-5:08** · "Officer and patron walk out of the library building towards the exteri"
- [ ] **video_19 2:54-4:18** · "Discussion continues regarding vehicle impoundment, rental car tracker"
- [ ] **video_19 5:45-7:03** · "Officer discussing vehicle impound and transport arrangements with ind"
- [ ] **video_19 9:24-10:17** · "And if they can't accommodate it, can you call Big Valley Towing?"
- [ ] **video_20 21:07-21:24** · "It's going to be towed."
- [ ] **video_20 25:56-26:19** · "Two officers conversing near the open door of the sedan regarding pape"
- [ ] **video_22 7:52-8:48** · "An individual in a grey long-sleeve shirt and cap points toward variou"
- [ ] **video_22 15:26-15:44** · "I said he just came to town two weeks ago."
- [ ] **video_23 0:17-1:07** · "The officer exits the patrol vehicle and walks across a grassy area to"
- [ ] **video_23 6:11-6:58** · "The civilian pointing toward different areas in the woods while speaki"
- [ ] **video_23 13:29-13:45** · "Deputies and the civilian walking away from the wooded area toward pat"
- [ ] **video_24 9:32-10:08** · "The officer walks toward a golf cart parked on the pathway while speak"
- [ ] **video_27 9:52-15:20** · "Dashcam view driving behind a tow truck on a rural highway during dayl"
- [ ] **video_27 16:45-18:43** · "A dark pickup truck pulls up and parks near the tow truck on the side "
- [ ] **video_27 19:52-25:26** · "Dashcam view of a parked police vehicle on the shoulder of a highway, "
- [ ] **video_28 0:00-0:17** · "Officer drives up a long paved driveway towards a large white mansion "
- [ ] **video_28 4:52-5:08** · "Officers walk around the exterior porch and stone pathways of the mans"
- [ ] **video_28 7:03-8:50** · "Officers and security walk the handcuffed individual up steps toward a"
- [ ] **video_28 11:43-12:40** · "Officers direct the handcuffed individual toward a patrol vehicle park"
- [ ] **video_29 0:08-0:26** · "Let's just step towards the back of the car, okay?"
- [ ] **video_29 4:24-5:08** · "Officers walk the driver away from the roadway toward police cruisers "
- [ ] **video_29 5:48-7:10** · "Officer walking the individual towards the rear of a police vehicle."
- [ ] **video_35 0:09-0:30** · "It's on Central Foot Pursuit going northbound towards Hickory."
- [ ] **video_35 7:24-8:56** · "The officer cleans the windshield of the police vehicle using paper to"
- [ ] **video_36 20:34-20:53** · "He went right to the middle of town in Dardanelle?"
- [ ] **video_39 11:47-12:18** · "The blue sedan briefly drifts towards the shoulder and navigates aroun"
- [ ] **video_9 5:07-5:38** · "The person walks away towards a parked silver sedan in a gravel drivew"
- [ ] **video_9 9:52-10:08** · "The individual gestures outward toward the driveway area while speakin"
- [ ] **video_9 14:52-15:08** · "The officer walks back along the driveway towards the parked police ve"

Truth YAML for kept boxes:
```yaml
  - query: a vehicle is towed or impounded
    type: direct
    truth:
      - {video: video_10, start: 21, end: 65}
      - {video: video_10, start: 525, end: 652}
      - {video: video_10, start: 678, end: 696}
      - {video: video_10, start: 1214, end: 1237}
      - {video: video_10, start: 1323, end: 1339}
      - {video: video_11, start: 0, end: 55}
      - {video: video_11, start: 827, end: 850}
      - {video: video_11, start: 1002, end: 1058}
      - {video: video_12, start: 6, end: 63}
      - {video: video_12, start: 505, end: 522}
      - {video: video_12, start: 604, end: 633}
      - {video: video_13, start: 843, end: 908}
      - {video: video_16, start: 0, end: 42}
      - {video: video_16, start: 351, end: 369}
      - {video: video_16, start: 466, end: 483}
      - {video: video_16, start: 580, end: 597}
      - {video: video_18, start: 3, end: 38}
      - {video: video_18, start: 292, end: 308}
      - {video: video_19, start: 174, end: 258}
      - {video: video_19, start: 345, end: 423}
      - {video: video_19, start: 564, end: 618}
      - {video: video_20, start: 1268, end: 1284}
      - {video: video_20, start: 1556, end: 1579}
      - {video: video_22, start: 472, end: 528}
      - {video: video_22, start: 926, end: 944}
      - {video: video_23, start: 17, end: 67}
      - {video: video_23, start: 371, end: 418}
      - {video: video_23, start: 809, end: 825}
      - {video: video_24, start: 572, end: 608}
      - {video: video_27, start: 592, end: 920}
      - {video: video_27, start: 1005, end: 1123}
      - {video: video_27, start: 1192, end: 1526}
      - {video: video_28, start: 0, end: 17}
      - {video: video_28, start: 292, end: 308}
      - {video: video_28, start: 423, end: 530}
      - {video: video_28, start: 703, end: 760}
      - {video: video_29, start: 9, end: 26}
      - {video: video_29, start: 264, end: 308}
      - {video: video_29, start: 348, end: 430}
      - {video: video_35, start: 10, end: 30}
      - {video: video_35, start: 444, end: 536}
      - {video: video_36, start: 1234, end: 1253}
      - {video: video_39, start: 707, end: 738}
      - {video: video_9, start: 307, end: 338}
      - {video: video_9, start: 592, end: 608}
      - {video: video_9, start: 892, end: 908}
```

## "an officer searches a vehicle"  (cross_modal)
- (scan proposed nothing - label by watching, or drop)

Truth YAML for kept boxes:
```yaml
  - query: an officer searches a vehicle
    type: cross_modal
    truth:
```

## "someone is placed in the back of a patrol car"  (cross_modal)
- [ ] **video_18 14:11-14:27** · "The officer opens the rear door of a police vehicle and organizes pape"
- [ ] **video_19 11:03-11:38** · "There's paperwork in the back seat."
- [ ] **video_24 5:51-7:12** · "The officer stops behind a golf cart and another police SUV, speaking "
- [ ] **video_28 0:47-1:10** · "Officer opens the rear door of a patrol vehicle and assists the handcu"
- [ ] **video_28 12:26-12:42** · "Watch your head."
- [ ] **video_28 14:52-15:08** · "Inside view of a patrol car while an officer checks on the detained pe"
- [ ] **video_28 18:08-18:42** · "Interior view from the back seat of a patrol vehicle showing an occupa"
- [ ] **video_36 23:52-24:09** · "Body-worn camera view shows the detained person seated in the back of "
- [ ] **video_38 24:42-25:08** · "An officer handles paperwork, checks a bag, and interacts with the per"
- [ ] **video_4 23:06-24:06** · "Inside view of the police cruiser backseat with the detained individua"

Truth YAML for kept boxes:
```yaml
  - query: someone is placed in the back of a patrol car
    type: cross_modal
    truth:
      - {video: video_18, start: 851, end: 867}
      - {video: video_19, start: 663, end: 698}
      - {video: video_24, start: 351, end: 432}
      - {video: video_28, start: 47, end: 70}
      - {video: video_28, start: 746, end: 763}
      - {video: video_28, start: 892, end: 908}
      - {video: video_28, start: 1088, end: 1122}
      - {video: video_36, start: 1432, end: 1449}
      - {video: video_38, start: 1482, end: 1508}
      - {video: video_4, start: 1386, end: 1446}
```

## "an officer asks about drugs or alcohol"  (direct)
- [ ] **video_24 17:02-17:26** · "send me up and stuff. I have my cigarette. What? Can I take a couple o"
- [ ] **video_28 17:55-18:19** · "Second one is for the possession of marijuana that you had in your pur"
- [ ] **video_35 21:25-21:43** · "Like maybe three drugs?"
- [ ] **video_36 13:16-13:35** · "You got drugs or anything on you?"
- [ ] **video_36 17:40-18:19** · "It looks like he's got a little marijuana on him."
- [ ] **video_36 22:32-22:49** · "How much marijuana do you smoke today?"
- [ ] **video_38 19:31-19:50** · "So my question is, how much have you had to drink tonight?"
- [ ] **video_38 22:30-22:50** · "If you have any drugs on your person and you enter the jail, it will b"

Truth YAML for kept boxes:
```yaml
  - query: an officer asks about drugs or alcohol
    type: direct
    truth:
      - {video: video_24, start: 1022, end: 1046}
      - {video: video_28, start: 1075, end: 1100}
      - {video: video_35, start: 1286, end: 1303}
      - {video: video_36, start: 796, end: 815}
      - {video: video_36, start: 1061, end: 1099}
      - {video: video_36, start: 1352, end: 1370}
      - {video: video_38, start: 1172, end: 1190}
      - {video: video_38, start: 1350, end: 1371}
```

## "a breathalyzer or breath test is given"  (direct)
- [ ] **video_20 16:56-17:14** · "to a breath test, to blow in a breathalyzer."
- [ ] **video_20 20:48-21:08** · "He's going to give you an opportunity to, to blow into a machine and i"
- [ ] **video_22 1:58-2:16** · "I was going to take this point out anyway."
- [ ] **video_36 21:42-23:23** · "An officer interacts with the detained person and prepares a breathaly"
- [ ] **video_9 3:23-3:41** · "So at this point of time, we have two victims, right?"
- [ ] **video_9 7:56-8:15** · "You know, at this point of time, it's up to investigators."

Truth YAML for kept boxes:
```yaml
  - query: a breathalyzer or breath test is given
    type: direct
    truth:
      - {video: video_20, start: 1017, end: 1034}
      - {video: video_20, start: 1248, end: 1268}
      - {video: video_22, start: 119, end: 136}
      - {video: video_36, start: 1302, end: 1403}
      - {video: video_9, start: 203, end: 222}
      - {video: video_9, start: 476, end: 495}
```

## "an officer talks to dispatch on the radio"  (direct)
- [ ] **video_10 11:54-12:11** · "We can't copy the key."
- [ ] **video_11 0:51-1:07** · "Copy."
- [ ] **video_11 2:05-2:21** · "10-4."
- [ ] **video_13 21:23-21:41** · "He needs a dispatcher medics, just PPD holding."
- [ ] **video_18 6:08-6:25** · "Free to copy and name and name again."
- [ ] **video_18 13:26-13:42** · "10-4."
- [ ] **video_19 2:04-2:20** · "Copy."
- [ ] **video_19 5:50-6:13** · "Copy, thanks."
- [ ] **video_19 6:58-7:18** · "If you could just write out a booking sheet, leave it in dispatch for "
- [ ] **video_19 10:02-10:18** · "Copy."
- [ ] **video_19 11:30-11:49** · "And then, um, just leave the booking sheet in dispatch."
- [ ] **video_20 1:44-2:03** · "Can you either pull it up on your phone, or do you have a copy of it o"
- [ ] **video_20 25:37-25:54** · "I was in dispatch."
- [ ] **video_27 9:21-10:06** · "10-4."
- [ ] **video_27 16:11-17:11** · "10-4."
- [ ] **video_28 0:00-0:17** · "That's 10-4, I'm at the house now."
- [ ] **video_28 2:01-3:08** · "That's 10-4."
- [ ] **video_28 4:20-4:37** · "10-4."
- [ ] **video_29 8:46-9:03** · "Dispatch actually 12."
- [ ] **video_35 4:58-6:01** · "10-4."
- [ ] **video_35 6:57-7:14** · "Free to copy one by SOC."
- [ ] **video_35 8:49-9:05** · "10-4."
- [ ] **video_35 10:35-10:53** · "He kept dispatching."
- [ ] **video_36 6:12-7:11** · "10-4 there guys."
- [ ] **video_36 9:27-9:46** · "10-4, he's on 247, heading to Potsy, Charger."
- [ ] **video_36 10:12-10:41** · "10-4."
- [ ] **video_36 11:09-11:43** · "10-4."
- [ ] **video_36 12:28-12:54** · "Copy."
- [ ] **video_38 16:52-17:12** · "Bravo 30, copy cable, head to stop, simply driven by the Black Mail."
- [ ] **video_4 8:43-9:00** · "Copy 27."
- [ ] **video_4 10:18-10:57** · "Copy that, boss."

Truth YAML for kept boxes:
```yaml
  - query: an officer talks to dispatch on the radio
    type: direct
    truth:
      - {video: video_10, start: 714, end: 732}
      - {video: video_11, start: 51, end: 68}
      - {video: video_11, start: 125, end: 142}
      - {video: video_13, start: 1283, end: 1301}
      - {video: video_18, start: 368, end: 385}
      - {video: video_18, start: 806, end: 823}
      - {video: video_19, start: 124, end: 140}
      - {video: video_19, start: 351, end: 373}
      - {video: video_19, start: 418, end: 438}
      - {video: video_19, start: 602, end: 618}
      - {video: video_19, start: 690, end: 709}
      - {video: video_20, start: 105, end: 124}
      - {video: video_20, start: 1537, end: 1554}
      - {video: video_27, start: 562, end: 606}
      - {video: video_27, start: 971, end: 1031}
      - {video: video_28, start: 0, end: 17}
      - {video: video_28, start: 121, end: 189}
      - {video: video_28, start: 261, end: 277}
      - {video: video_29, start: 526, end: 543}
      - {video: video_35, start: 298, end: 362}
      - {video: video_35, start: 417, end: 434}
      - {video: video_35, start: 529, end: 546}
      - {video: video_35, start: 635, end: 654}
      - {video: video_36, start: 373, end: 431}
      - {video: video_36, start: 568, end: 587}
      - {video: video_36, start: 612, end: 641}
      - {video: video_36, start: 669, end: 704}
      - {video: video_36, start: 748, end: 774}
      - {video: video_38, start: 1013, end: 1032}
      - {video: video_4, start: 524, end: 541}
      - {video: video_4, start: 619, end: 657}
```

## "a weapon is found or discussed"  (cross_modal)
- [ ] **video_13 2:23-2:40** · "Do you have any weapons on you?"
- [ ] **video_13 3:37-3:54** · "You got any weapons on him?"
- [ ] **video_13 23:12-25:12** · "bottle, knife, person"
- [ ] **video_16 3:56-4:14** · "Do you have any weapons on you or anything else I need to know about?"
- [ ] **video_16 10:42-10:58** · "knife"
- [ ] **video_19 0:37-1:10** · "Do you have any weapons on you?"
- [ ] **video_19 13:46-14:04** · "Yeah, that's why I took my weapon off everything."
- [ ] **video_22 2:50-3:49** · "Do you mind flipping your bag over so I make sure you don't have any w"
- [ ] **video_23 0:42-1:45** · "You got any weapons on you?"
- [ ] **video_23 8:00-9:00** · "at him with the gun too."
- [ ] **video_23 9:34-9:53** · "report too as far as you coming out here with the gun shooting at him "
- [ ] **video_24 22:42-23:11** · "He's got a gun."
- [ ] **video_29 5:23-5:47** · "I'm going to take a pocket knife."
- [ ] **video_29 6:16-6:35** · "Just to say, I know the knife, but it's closed. Pocket knife, right?"
- [ ] **video_36 12:22-12:39** · "We got him out of gun."
- [ ] **video_38 15:08-15:38** · "knife, person"
- [ ] **video_39 1:13-1:31** · "Gun Number"
- [ ] **video_9 0:12-0:32** · "and they think that he wasn't wearing a gun and gloves as well, yes."
- [ ] **video_9 12:09-12:28** · "He believes he got a gun."
- [ ] **video_9 15:31-16:09** · "I cannot even see whether he had a gun or glass."

Truth YAML for kept boxes:
```yaml
  - query: a weapon is found or discussed
    type: cross_modal
    truth:
      - {video: video_13, start: 144, end: 161}
      - {video: video_13, start: 218, end: 235}
      - {video: video_13, start: 1392, end: 1512}
      - {video: video_16, start: 236, end: 254}
      - {video: video_16, start: 642, end: 658}
      - {video: video_19, start: 37, end: 71}
      - {video: video_19, start: 827, end: 845}
      - {video: video_22, start: 170, end: 230}
      - {video: video_23, start: 43, end: 105}
      - {video: video_23, start: 480, end: 540}
      - {video: video_23, start: 574, end: 593}
      - {video: video_24, start: 1363, end: 1392}
      - {video: video_29, start: 323, end: 347}
      - {video: video_29, start: 376, end: 395}
      - {video: video_36, start: 742, end: 759}
      - {video: video_38, start: 908, end: 938}
      - {video: video_39, start: 74, end: 91}
      - {video: video_9, start: 13, end: 33}
      - {video: video_9, start: 730, end: 748}
      - {video: video_9, start: 932, end: 970}
```

## "someone refuses to identify themselves"  (direct)
- (scan proposed nothing - label by watching, or drop)

Truth YAML for kept boxes:
```yaml
  - query: someone refuses to identify themselves
    type: direct
    truth:
```

## "a car crash or collision scene"  (cross_modal)
- [ ] **video_22 4:54-5:12** · "So, you don't have a house or anything that you crash at?"
- [ ] **video_27 6:25-6:44** · "I don't know. I can't see him in there because of airbags."
- [ ] **video_39 12:43-12:59** · "Multiple law enforcement officers converge on the scene and approach t"

Truth YAML for kept boxes:
```yaml
  - query: a car crash or collision scene
    type: cross_modal
    truth:
      - {video: video_22, start: 294, end: 312}
      - {video: video_27, start: 386, end: 404}
      - {video: video_39, start: 763, end: 779}
```

## "an officer speaks spanish with someone"  (direct)
- (scan proposed nothing - label by watching, or drop)

Truth YAML for kept boxes:
```yaml
  - query: an officer speaks spanish with someone
    type: direct
    truth:
```

