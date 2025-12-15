// Table styling defaults for Typst output
// Subtle borders, comfortable padding, shaded header row, zebra striping
#show table: set table(
  inset: 6pt,
  stroke: (x: 0.5pt, y: 0.5pt, rest: luma(220)),
)

#show table.cell: set table.cell(
  inset: (x: 6pt, y: 4pt),
  align: left,
)

// Header row styling (first row)
#show table.cell.where(y: 0): set table.cell(
  fill: luma(240),
)

// Zebra striping for odd-numbered body rows (apply to rows 1..49)
// We enumerate odd row selectors explicitly because Typst expressions
// for modular arithmetic aren't supported in this context.
#show table.cell.where(y: 1): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 3): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 5): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 7): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 9): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 11): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 13): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 15): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 17): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 19): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 21): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 23): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 25): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 27): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 29): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 31): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 33): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 35): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 37): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 39): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 41): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 43): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 45): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 47): set table.cell(
  fill: luma(248),
)
#show table.cell.where(y: 49): set table.cell(
  fill: luma(248),
)
