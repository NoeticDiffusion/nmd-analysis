// Network Neuroscience Typst Template
// Based on official guidelines and recent publications.

#let clean-table(
  columns: auto,
  header: (),
  align: left,
  inset: 5pt,
  text-size: 9pt,
  leading: 1.2em,
  midrule: 0.5pt + black,
  ..body,
) = context {
  set text(size: text-size)
  set par(
    first-line-indent: 0pt,
    leading: leading,
  )
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

#let netn-template(
  title: "",
  short-title: "",
  subtitle: none,
  authors: (),
  affiliations: (),
  corresponding-author: "",
  keywords: (),
  article-type: "Research",
  abstract: [],
  author-summary: none,
  author-contributions: none,
  funding-info: none,
  data-availability: none,
  competing-interests: "The authors have declared that no competing interests exist.",
  body
) = {
  set page(
    paper: "us-letter",
    margin: (x: 1in, y: 1in),
    numbering: "1",
    header: context {
      if counter(page).get().first() > 1 {
        set text(size: 9pt, style: "italic")
        if short-title != "" {
          short-title
        } else {
          title
        }
        h(1fr)
        counter(page).display()
      }
    }
  )

  set text(
    font: "Times New Roman",
    size: 12pt,
  )

  show table: it => {
    set text(size: 9pt)
    set par(
      first-line-indent: 0pt,
      leading: 1.2em,
    )
    show table.cell: set table.cell(stroke: none)
    show table.cell.where(y: 0): set table.cell(stroke: (bottom: 0.5pt + black))
    it
  }

  set par(
    justify: true,
    first-line-indent: 0.5in,
    leading: 1.8em,
  )

  show figure.caption: set text(size: 10pt, style: "italic")
  show figure.caption: set par(leading: 1.15em)

  set heading(numbering: none)
  show heading: it => {
    set block(above: 1.5em, below: 1em)
    if it.level == 1 {
      set text(size: 14pt, weight: "bold")
      it
    } else if it.level == 2 {
      set text(size: 12pt, weight: "bold")
      it
    } else {
      set text(size: 12pt, weight: "bold", style: "italic")
      it
    }
  }

  align(center)[
    #text(size: 10pt)[Article type: #article-type] \
    #v(1em)
    #text(size: 18pt, weight: "bold")[#title] \
    #if subtitle != none {
      text(size: 14pt, style: "italic")[#subtitle]
      linebreak()
    }
    #v(1em)
    #text(size: 10pt)[Short title: #short-title] \
    #v(1.5em)

    #let author-names = authors.map(a => {
      a.name + super(str(a.affil))
    }).join(", ")
    #text(size: 11pt)[#author-names] \
    #v(0.5em)

    #let affil-list = affiliations.enumerate().map(a => {
      super(str(a.at(0) + 1)) + " " + a.at(1)
    }).join("; ")
    #text(size: 9pt, style: "italic")[#affil-list] \
    #v(1em)

    #text(size: 10pt)[Corresponding author: #corresponding-author] \
    #v(1em)

    #text(size: 10pt)[Keywords: #keywords.join(", ")]
  ]

  v(2em)

  if abstract != [] {
    heading(level: 1)[Abstract]
    par(first-line-indent: 0pt)[#abstract]
  }

  if author-summary != none {
    v(1.5em)
    heading(level: 1)[Author Summary]
    par(first-line-indent: 0pt)[#author-summary]
  }

  v(2em)

  show heading: it => {
    it
    par(first-line-indent: 0pt)[#text(size: 0pt, h(0pt))]
  }

  body

  if author-contributions != none {
    heading(level: 1)[Author Contributions]
    author-contributions
  }

  if funding-info != none {
    heading(level: 1)[Funding Information]
    funding-info
  }

  if data-availability != none {
    heading(level: 1)[Data Availability Statement]
    data-availability
  }

  if competing-interests != none {
    heading(level: 1)[Competing Interests]
    competing-interests
  }
}

#let technical-terms(terms) = {
  heading(level: 1)[Technical Terms]
  for (term, definition) in terms {
    par(first-line-indent: 0pt)[
      *#term*: #definition
    ]
  }
}

#let netn-box(title: none, body) = {
  block(
    width: 100%,
    fill: luma(245),
    inset: 1em,
    stroke: 0.5pt + luma(100),
    radius: 4pt,
  )[
    #if title != none {
      text(weight: "bold")[#title]
      v(0.5em)
    }
    #body
  ]
}
