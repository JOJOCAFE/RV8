export const labs = [
  {
    id: "loop",
    name: "Make a loop",
    title: "Make the light work. You build the circuit.",
    goal: "Make a continuous route from battery +, through the lamp, back to battery −.",
    parts: ["battery", "lamp"],
    switches: [],
    concept: "Electricity needs a complete route.",
    teaching:
      "A battery supplies electrical energy through two terminals, + and −. A terminal is a place to attach a wire. The lamp has two ends joined by a thin wire inside it, called a filament. The filament turns electrical energy into heat and light. A wire between two terminals connects them. For this lamp to glow, its filament must be part of a complete route between the battery terminals.",
    task: "Add a battery and a lamp. Connect their terminals with your own wires. Then predict what you’ll see and test it.",
    hints: [
      "Look inside the lamp symbol. The zigzag filament already connects its two ends. What is still missing outside it?",
      "A wire to only one lamp end leaves the other end disconnected. Follow the whole route, including the way back.",
      "Use two wires: connect battery + to one lamp end, and connect the other lamp end to battery −. You still need to draw both wires.",
    ],
    question: "Both lamp ends are connected to battery +. What do you predict?",
    answers: [
      "On, because both ends have a wire.",
      "Off, because both ends have the same connection.",
    ],
    correct: 1,
    feedback:
      "The two ends must connect to different battery terminals, with the filament between them. Wire count alone does not establish a complete useful circuit.",
    takeaway:
      "You made a loop, broke it, and repaired it. A connection only works as part of the whole route.",
  },
  {
    id: "control",
    name: "Control it",
    title: "Make a switch control your lamp.",
    goal: "The lamp must be off when switch A is open, and on when A is closed.",
    parts: ["battery", "lamp", "A"],
    switches: ["A"],
    concept: "A switch makes or breaks one connection.",
    teaching:
      "The switch symbol shows its metal contact. Open means the two ends do not touch. Closed means they do. Closing a switch can complete a route—but only if your wiring makes that switch part of the route.",
    task: "Keep your circuit. Add switch A and decide where to put its two ends. A switch connected beside the route might do nothing.",
    hints: [
      "If your lamp stays on with A open, trace its route. Does the route actually pass through A?",
      "Opening A must remove the only complete route through the lamp. Any wire around A defeats that job.",
      "Remove one existing wire. Replace that connection with a route that goes through both ends of switch A.",
    ],
    question:
      "You add a wire straight across the two ends of A. A is open. What happens?",
    answers: [
      "The lamp must be off because A is open.",
      "The lamp can stay on through the new wire.",
    ],
    correct: 1,
    feedback:
      "An open switch blocks its own contact. It cannot block a different wire that goes around it.",
    takeaway:
      "You made an input control an output, and proved that an open switch only matters if it interrupts the route.",
  },
  {
    id: "both",
    name: "Make both necessary",
    title: "Can you make two switches necessary?",
    goal: "The lamp turns on only when A and B are both closed. Every other setting must leave it off.",
    parts: ["battery", "lamp", "A", "B"],
    switches: ["A", "B"],
    concept: "Use the route to create a rule.",
    teaching:
      "You already know how one switch breaks a route. This time each of two switches must be able to break it. Decide how to join them. The table below lists every possible input setting; one successful setting is not enough to prove your design.",
    task: "Add B. Build your own route, predict each setting, then collect all four observations.",
    hints: [
      "Try opening A with B closed. If the lamp stays on, there is a route that does not need A.",
      "Now do the reverse. If either switch is required, the complete route must go through both contacts.",
      "Put A and B one after the other in the same route. This arrangement is called series.",
    ],
    question:
      "Your circuit works with A and B closed. Is that enough evidence?",
    answers: [
      "Yes, because the lamp lit up.",
      "No. Either switch alone might also let it light.",
    ],
    correct: 1,
    feedback:
      "To establish “both are necessary”, you must also test A alone, B alone, and neither. The off results are part of the evidence.",
    takeaway:
      "Your wiring implements AND: output on only when both inputs are on. You built the rule before giving it a name.",
  },
  {
    id: "either",
    name: "Make either enough",
    title: "Now make either switch enough.",
    goal: "A alone must light the lamp. B alone must also light it. Neither means off; both means on.",
    parts: ["battery", "lamp", "A", "B"],
    switches: ["A", "B"],
    concept: "More than one route is possible.",
    teaching:
      "The previous circuit needed both contacts. Now think about an alternative route: when one contact is open, can the other still complete a route through the lamp? The parts are the same. The wiring decides the rule.",
    task: "Rewire your own circuit. Keep the battery and lamp; change how A and B connect. Test every setting again.",
    hints: [
      "Follow the successful path with A alone closed. It must avoid B’s open contact.",
      "Then follow the successful path with B alone closed. It must avoid A’s open contact.",
      "Give A and B separate branches between the same two connection points. This arrangement is called parallel.",
    ],
    question: "A branch contains an open switch. Must the lamp be off?",
    answers: [
      "Always: any open switch stops the whole circuit.",
      "It depends on whether another complete route exists.",
    ],
    correct: 1,
    feedback:
      "An alternative branch can still supply a complete route through the lamp. You must inspect the whole wiring.",
    takeaway:
      "Your wiring implements OR: either input can make the output on. The rule came from the available routes.",
  },
  {
    id: "transfer",
    name: "Build a new rule",
    title: "Use what you learned. Build a new rule.",
    goal: "A and B must work together. C must also be able to light the lamp on its own.",
    parts: ["battery", "lamp", "A", "B", "C"],
    switches: ["A", "B", "C"],
    concept: "Combine rules you have already built.",
    teaching:
      "No new kind of part is needed. Reuse the two route ideas you discovered: contacts that are both required, and alternative branches. This time there are eight settings to investigate.",
    task: "Add C and design the wiring yourself. Your goal is (A AND B) OR C. Prove it with all eight experiments.",
    hints: [
      "Start with C open. The circuit should behave like your “both necessary” design.",
      "Now close C and open A and B. C needs its own complete route through the lamp.",
      "Make one branch containing A then B, and a separate branch containing C. Both branches must still go through the lamp.",
    ],
    question:
      "C is closed, A is open, B is closed. Why should your lamp be on?",
    answers: [
      "C provides a complete alternative route.",
      "B is closed, so A no longer matters in its branch.",
    ],
    correct: 0,
    feedback:
      "A still breaks the A–B branch. The independent C branch is what keeps the lamp on.",
    takeaway:
      "You combined two behaviors into a new one, built the connections yourself, and checked every input case.",
  },
];
export const partInfo = {
  battery: {
    name: "Battery",
    detail: "Supplies two different terminal levels: + and −.",
    icon: "＋ ┃ −",
  },
  lamp: {
    name: "Lamp",
    detail: "Its visible filament joins its two terminals.",
    icon: "◉",
  },
  A: {
    name: "Switch A",
    detail: "Open contact breaks its connection; closed joins it.",
    icon: "A",
  },
  B: {
    name: "Switch B",
    detail: "Another contact. You decide where it belongs.",
    icon: "B",
  },
  C: {
    name: "Switch C",
    detail: "A third contact for your own combined rule.",
    icon: "C",
  },
};
