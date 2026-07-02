// Template for eLife-style Typst articles
// Extracted from the original example so manuscripts can stay focused on content.

#let note-line(label, body) = par(first-line-indent: 0pt)[
  #emph(label)#text(": ")#body
]

#let supplement-box(title, body) = block(
  inset: 10pt,
  stroke: 0.5pt + black,
  above: 8pt,
  below: 8pt,
)[
  #par(first-line-indent: 0pt)[#strong(title)]
  #body
]

#let abstract-block(body) = block(
  stroke: (
    top: 0.8pt + black,
    bottom: 0.8pt + black,
  ),
  inset: (
    top: 8pt,
    bottom: 8pt,
  ),
  above: 12pt,
  below: 14pt,
)[
  #grid(
    columns: (auto, 1fr),
    column-gutter: 10pt,
    align: (left, top),
    [#par(first-line-indent: 0pt)[#strong[Abstract]]],
    [
      #set par(first-line-indent: 0pt)
      #body
    ],
  )
]

#let clean-table(
  columns: auto,
  header: (),
  align: left,
  inset: 5pt,
  midrule: 0.5pt + black,
  ..body,
) = context {
  set text(size: 8.2pt)
  table(
    columns: columns,
    inset: inset,
    align: align,
    stroke: none,
    table.header(..header),
    table.hline(y: 1, stroke: midrule),
    ..body,
  )
}

#let netn-box(title: none, body) = block(
  inset: 10pt,
  stroke: 0.5pt + black,
  above: 8pt,
  below: 8pt,
)[
  #if title != none {
    par(first-line-indent: 0pt)[#strong(title)]
    v(4pt)
  }
  #body
]

#let technical-terms(terms) = {
  heading(level: 1)[Technical Terms]
  for (term, definition) in terms {
    par(first-line-indent: 0pt)[
      *#term*: #definition
    ]
  }
}

#let elife-template(
  title: none,
  authors: none,
  affiliations: none,
  correspondence: none,
  contributor_notes: none,
  abstract: none,
  doc,
) = {
  set page(
    paper: "a4",
    margin: (
      left: 5cm,
      right: 2cm,
      top: 2.2cm,
      bottom: 2.2cm,
    ),
  )

  set text(
    font: "Times New Roman",
    size: 9pt,
  )

  set par(
    justify: true,
    first-line-indent: 1.5em,
    leading: 0.72em,
  )

  set heading(numbering: none)
  set math.equation(numbering: "(1)")

  // eLife-style tables: no cell fill, no grid, single rule under header.
  show table: it => {
    set text(size: 8.2pt)
    set par(
      first-line-indent: 0pt,
      leading: 1.2em,
    )
    show table.cell: set table.cell(stroke: none, fill: none)
    show table.cell.where(y: 0): set table.cell(stroke: (bottom: 0.5pt + black), fill: none)
    it
  }

  show figure.caption: set text(size: 8pt)
  show figure.caption: set par(first-line-indent: 0pt, leading: 1.15em)

  if title != none {
    align(center)[
      #text(size: 16pt, weight: "bold")[#title]
    ]

    if contributor_notes != none {
      set text(size: 8pt)
      contributor_notes
      set text(size: 9pt)
    }

    v(10pt)
  }

  if authors != none {
    par(first-line-indent: 0pt)[#authors]
  }

  if affiliations != none {
    affiliations
  }

  if correspondence != none {
    set text(size: 8pt)
    par(first-line-indent: 0pt)[#strong[For correspondence:] #correspondence]
    set text(size: 9pt)
  }

  if abstract != none {
    abstract-block(abstract)
  }

  doc
}

#let netn-template(
  title: "",
  short-title: "",
  subtitle: none,
  authors: (),
  affiliations: (),
  corresponding-author: "",
  keywords: (),
  article-type: "Research",
  abstract: none,
  author-summary: none,
  author-contributions: none,
  funding-info: none,
  data-availability: none,
  competing-interests: none,
  body,
) = {
  let author-line = if authors == () {
    none
  } else {
    authors.map(a => a.name + super(str(a.affil))).join(", ")
  }

  let affil-block = if affiliations == () {
    none
  } else {
    block(above: 4pt, below: 4pt)[
      #set text(size: 8pt)
      #set par(first-line-indent: 0pt)
      #for (idx, affil) in affiliations.enumerate() {
        [#super(str(idx + 1)) #affil]
        if idx < affiliations.len() - 1 {
          linebreak()
        }
      }
      #set text(size: 9pt)
    ]
  }

  let contributor-block = [
    #par(first-line-indent: 0pt)[Article type: #article-type]
    #if short-title != "" {
      par(first-line-indent: 0pt)[Short title: #short-title]
    }
    #if keywords != () and keywords != none {
      par(first-line-indent: 0pt)[Keywords: #keywords.join(", ")]
    }
  ]

  elife-template(
    title: title,
    authors: author-line,
    affiliations: affil-block,
    correspondence: corresponding-author,
    contributor_notes: [
      #if subtitle != none {
        align(center)[
          #par(first-line-indent: 0pt)[#emph(subtitle)]
        ]
        v(4pt)
      }
      #contributor-block
    ],
    abstract: abstract,
    [
      #if author-summary != none {
        heading(level: 1)[Author Summary]
        par(first-line-indent: 0pt)[#author-summary]
        v(1em)
      }

      #body

      #if author-contributions != none {
        heading(level: 1)[Author Contributions]
        author-contributions
      }

      #if funding-info != none {
        heading(level: 1)[Funding Information]
        funding-info
      }

      #if data-availability != none {
        heading(level: 1)[Data Availability Statement]
        data-availability
      }

      #if competing-interests != none {
        heading(level: 1)[Competing Interests]
        competing-interests
      }
    ],
  )
}
