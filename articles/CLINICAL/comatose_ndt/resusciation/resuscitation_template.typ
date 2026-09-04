#let clean-table(
  columns: auto,
  align: left,
  inset: 4pt,
  text-size: 9pt,
  ..body,
) = {
  set text(size: text-size)
  set table(stroke: none)
  set par(first-line-indent: 0pt, leading: 1.15em)
  table(
    columns: columns,
    align: align,
    inset: inset,
    stroke: none,
    table.hline(y: 1, stroke: 0.5pt + black),
    ..body,
  )
}

#let resuscitation-template(
  title: "",
  short-title: "",
  authors: (),
  affiliations: (),
  corresponding-author: "",
  keywords: (),
  article-type: "Original paper",
  abstract: none,
  line-numbers: false,
  show-summary: true,
  body,
) = {
  set page(
    paper: "a4",
    margin: (x: 22mm, y: 22mm),
    numbering: "1",
    footer: context align(right)[#counter(page).display("1")],
  )
  set text(font: "Times New Roman", size: 11pt)
  set par(justify: true, first-line-indent: 0pt, leading: 1.35em)
  if line-numbers {
    set par.line(
      numbering: "1",
      numbering-scope: "page",
      number-margin: left,
      number-align: right,
    )
  }
  set heading(numbering: "1.1")
  show heading.where(level: 1): it => {
    set text(size: 13pt, weight: "bold")
    set block(above: 1.4em, below: 0.6em)
    it
  }
  show heading.where(level: 2): it => {
    set text(size: 11pt, weight: "bold")
    set block(above: 1em, below: 0.4em)
    it
  }
  show figure.caption: set text(size: 9pt)
  show figure.caption: set par(first-line-indent: 0pt, leading: 1.1em)

  align(center)[
    #text(size: 17pt, weight: "bold")[#title]
    #if authors.len() > 0 {
      v(0.8em)
      let author-names = authors.map(a => a.name + super(str(a.affil))).join(", ")
      text(size: 10pt)[#author-names]
      v(0.4em)
      let affil-list = affiliations.enumerate().map(a => super(str(a.at(0) + 1)) + " " + a.at(1)).join("; ")
      text(size: 9pt)[#affil-list]
      if corresponding-author != "" {
        v(0.4em)
        text(size: 9pt)[Corresponding author: #corresponding-author]
      }
    }
  ]

  if show-summary {
    if abstract != none {
      v(1.2em)
      text(weight: "bold")[Abstract]
      par(first-line-indent: 0pt)[#abstract]
    }
    if keywords.len() > 0 {
      v(0.5em)
      par(first-line-indent: 0pt)[*Keywords:* #keywords.join(", ")]
    }
    if abstract != none or keywords.len() > 0 {
      v(1em)
    }
  }
  body
}
