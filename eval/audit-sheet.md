# Truth-span audit sheet

Jump to each timestamp, watch about twenty seconds, and keep the
box only if the event is really there. Strike the rest.

## "officer reads someone their rights"  (direct)
- [ ] **video_19 7:15-7:35** · "And you can either hire an attorney or come back and talk to the judge"

Truth YAML for kept boxes:
```yaml
  - query: officer reads someone their rights
    type: direct
    truth:
      - {video: video_19, start: 435, end: 455}
```

## "officer orders the driver to step out of the vehicle"  (direct)
- [ ] **video_16 2:52-3:10** · "Alright, Ms. Diaz, I need you to step out the car."
- [ ] **video_16 4:35-4:58** · "Can you step out for me real quick, my man?"
- [ ] **video_18 2:54-3:13** · "How about if I step outside and I'll wait for your sergeant to get her"
- [ ] **video_19 1:28-1:45** · "Do you want me to go out of the car?"
- [ ] **video_29 0:00-0:18** · "Are you able to step out with me?"
- [ ] **video_29 2:46-3:20** · "Chase, so the reason why we pulled you out of the car..."
- [ ] **video_29 5:34-5:53** · "Is there anything out of the car that you need your wallet? Anything l"

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
```

## "a person is being handcuffed"  (cross_modal)
- [ ] **video_16 2:52-5:08** · "The female driver is instructed to exit the vehicle and is handcuffed "
- [ ] **video_16 14:52-16:23** · "An adult female with long dark hair, wearing a green hoodie and sweatp"
- [ ] **video_18 2:24-2:42** · "to get you in handcuffs and arrested."
- [ ] **video_19 0:34-1:13** · "The officer directs the driver to face the vehicle and places him in c"
- [ ] **video_22 3:44-4:02** · "Just put your hands behind your back right there."

Truth YAML for kept boxes:
```yaml
  - query: a person is being handcuffed
    type: cross_modal
    truth:
      - {video: video_16, start: 172, end: 308}
      - {video: video_16, start: 892, end: 983}
      - {video: video_18, start: 145, end: 162}
      - {video: video_19, start: 34, end: 73}
      - {video: video_22, start: 225, end: 242}
```

## "a vehicle stopped by police at night"  (cross_modal)
- [ ] **video_16 0:00-0:14** · "An officer driving a police vehicle during a traffic stop, approaching"
- [ ] **video_16 4:52-5:23** · "A man in a black t-shirt with text standing outside a blue car during "
- [ ] **video_19 0:00-0:50** · "An officer conducts a traffic stop on a highway in bright daylight, in"
- [ ] **video_19 9:52-10:26** · "An officer stands near a white sports car on the shoulder of a highway"
- [ ] **video_29 0:00-0:21** · "An officer interacts with a driver seated inside a pickup truck during"

Truth YAML for kept boxes:
```yaml
  - query: a vehicle stopped by police at night
    type: cross_modal
    truth:
      - {video: video_16, start: 0, end: 14}
      - {video: video_16, start: 292, end: 323}
      - {video: video_19, start: 0, end: 50}
      - {video: video_19, start: 592, end: 626}
      - {video: video_29, start: 0, end: 21}
```

## "someone raises their voice"  (cross_modal)
- [ ] **video_12 8:04-9:48** · "Officers and a firefighter in a yellow vest converse on the paved lot "
- [ ] **video_9 9:42-10:08** · "The officer holds a stack of yellow legal pads with handwritten notes,"

Truth YAML for kept boxes:
```yaml
  - query: someone raises their voice
    type: cross_modal
    truth:
      - {video: video_12, start: 484, end: 588}
      - {video: video_9, start: 582, end: 608}
```

## "a field sobriety test is conducted"  (cross_modal)
- [ ] **video_29 3:06-3:24** · "Would you be willing to do some sobriety exercises for us tonight?"
- [ ] **video_29 4:29-5:06** · "We do the field sobriety exercises."

Truth YAML for kept boxes:
```yaml
  - query: a field sobriety test is conducted
    type: cross_modal
    truth:
      - {video: video_29, start: 186, end: 205}
      - {video: video_29, start: 270, end: 306}
```

