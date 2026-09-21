const colors = [
  "blue",
  "indigo",
  "green",
  "emerald",
  "teal",
  "purple",
  "violet",
  "orange",
  "amber",
  "yellow",
  "red",
  "rose",
  "sky",
  "slate",
];
module.exports = {
  content: [],
  darkMode: "class",
  safelist: [
    "grid-cols-4",
    "grid-cols-5",
    ...colors.flatMap((c) =>
      ["bg", "text", "border", "from", "to"].flatMap((p) =>
        [50, 100, 200, 300, 400, 500, 600, 700, 800, 900].map(
          (n) => `${p}-${c}-${n}`,
        ),
      ),
    ),
  ],
};
