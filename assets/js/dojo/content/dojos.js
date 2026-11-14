/**
 * The two dojo at the crossroads. A closed dojo shows its "under repair" tag and
 * the gatekeeper turns you away; opening one is a matter of flipping `open`.
 */
export const DOJOS = {
  read: { id: "read", side: "left", ja: "読解道場", kanji: "読", g: ["Reading Dojo", "讀解道場"], labelKey: "readingDojo", section: "reading", open: true },
  listen: { id: "listen", side: "right", ja: "聴解道場", kanji: "聴", g: ["Listening Dojo", "聽解道場"], labelKey: "listeningDojo", section: "listening", open: false },
};

export const dojoForSide = (side) => (side === "left" ? DOJOS.read : DOJOS.listen);
