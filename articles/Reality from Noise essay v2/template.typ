// Template for "The Symphony of Being" essay
// Professional formatting with LaTeX-like appearance

// Same contract as NoeticDiffusionTheory_v2/template_eLife.typ: no cell grid.
// The header rule is applied by the show table rule in essay-template.
#let clean-table(
  columns: auto,
  align: left,
  inset: 5pt,
  midrule: 0.5pt + black,
  ..body,
) = table(
  columns: columns,
  inset: inset,
  align: align,
  stroke: none,
  fill: none,
  table.hline(y: 1, stroke: midrule),
  ..body,
)

#let essay-template(
  title: none,
  subtitle: none,
  author: none,
  date: none,
  series-description: [A journey into Noetic Diffusion Theory and the\ Reconstructive Theory of Being],
  doc,
) = {
  // Page setup
  set page(
    paper: "a4",
    margin: (
      top: 2.5cm,
      bottom: 2.5cm,
      left: 2.5cm,
      right: 2.5cm,
    ),
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 1 {
        align(right)[
          #text(size: 9pt, style: "italic")[Reality from Noise]
          #h(1fr)
          #page-num
        ]
      }
    },
    numbering: "1",
  )
  
  // Text setup
  set text(
    font: "New Computer Modern",
    size: 11pt,
    lang: "en",
    hyphenate: true,
  )
  
  // Paragraph setup
  set par(
    justify: true,
    leading: 0.65em,
    first-line-indent: 1.2em,
  )

  // Enable chapter numbering for level-1 headings only
  set heading(numbering: "1.")
  
  // Heading styles
  show heading.where(level: 1): it => {
    set text(size: 18pt, weight: "bold")
    set block(above: 1.8em, below: 1.2em)
    align(left)[
      #it
    ]
  }
  
  show heading.where(level: 2): it => {
    set text(size: 13pt, weight: "semibold")
    set block(above: 1.4em, below: 0.8em)
    it
  }
  
  show heading.where(level: 3): it => {
    set text(size: 11pt, weight: "semibold", style: "italic")
    set block(above: 1em, below: 0.5em)
    it
  }
  
  // Math equation styling
  set math.equation(numbering: "(1)")
  
  // Quote/emphasis styling
  show emph: it => text(style: "italic", it.body)
  show strong: it => text(weight: "bold", it.body)
  
  // Link styling
  show link: it => text(fill: rgb("#0066cc"), it)

  // Code/technical term styling  
  show raw.where(block: false): it => box(
    fill: luma(240),
    inset: (x: 3pt, y: 0pt),
    outset: (y: 3pt),
    radius: 2pt,
    text(font: ("Courier New", "DejaVu Sans Mono", "Consolas"), size: 0.9em, it)
  )

  // eLife/NDT tables: no cell fill, no grid, single rule under the header.
  // Table-level stroke: none is required so a bare #table(...) cannot fall
  // back to Typst's default 1pt cell grid.
  show table: it => {
    set table(stroke: none, fill: none)
    set par(first-line-indent: 0pt, leading: 0.8em)
    show table.cell: set table.cell(stroke: none, fill: none)
    show table.cell.where(y: 0): set table.cell(
      stroke: (bottom: 0.5pt + black),
      fill: none,
    )
    it
  }
  
  // Title page
  if title != none {
    set align(center)
    v(2cm)
    
    text(size: 24pt, weight: "bold")[#title]
    
    if subtitle != none {
      v(0.8em)
      text(size: 16pt, style: "italic")[#subtitle]
    }
    
    v(2em)
    
    if author != none {
      text(size: 12pt)[#author]
    }
    
    v(1em)
    
    if date != none {
      text(size: 10pt)[#date]
    }
    
    v(1.5cm)
    
    text(size: 10pt, style: "italic")[
      #series-description
    ]
    
    v(1em)
    
    text(size: 9pt, style: "italic")[
      Developed through collaborative human-AI dialogue and external peer review.
    ]

    text(size: 9pt, style: "italic")[
      Version 0.6, DOI: `10.5281/zenodo.18600514`
    ]
    
    pagebreak()
  }
  
  // Reset paragraph indent for first paragraph after headings
  show heading: it => {
    it
    par(first-line-indent: 0em)[#text(size: 0pt)[]]
  }
  
  // Document body
  doc
}

