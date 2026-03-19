const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
        BorderStyle, WidthType, ShadingType, PageNumber, PageBreak } = require("docx");
const fs = require("fs");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function headerCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: { fill: "1B2A4A", type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", font: "Arial", size: 20 })] })]
  });
}

function cell(text, width, opts = {}) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, ...opts })] })]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: "1B2A4A" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: "2E5090" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "3A6EA5" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "\u25E6", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
      ]},
      { reference: "numbers", levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
      ]},
    ]
  },
  sections: [
    // ===== COVER PAGE =====
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      children: [
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [
          new TextRun({ text: "LATENCY EDGE", font: "Arial", size: 56, bold: true, color: "1B2A4A" })
        ]}),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [
          new TextRun({ text: "Paper Trading System", font: "Arial", size: 32, color: "666666" })
        ]}),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [
          new TextRun({ text: "\u2500".repeat(40), color: "CCCCCC", size: 20 })
        ]}),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [
          new TextRun({ text: "Technical Architecture & Algorithm Documentation", font: "Arial", size: 22, color: "888888" })
        ]}),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600 }, children: [
          new TextRun({ text: "2026.03", font: "Arial", size: 24, color: "888888" })
        ]}),
      ]
    },

    // ===== MAIN CONTENT =====
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      headers: {
        default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [
          new TextRun({ text: "Latency Edge \u2014 Technical Documentation", font: "Arial", size: 16, color: "999999" })
        ]})] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: "Page ", font: "Arial", size: 16, color: "999999" }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }),
        ]})] })
      },
      children: [
        // === 1. OVERVIEW ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. \uD504\uB85C\uC81D\uD2B8 \uAC1C\uC694")] }),
        new Paragraph({ spacing: { after: 200 }, children: [
          new TextRun("Latency Edge\uB294 "),
          new TextRun({ text: "\uBC14\uC774\uB09C\uC2A4(Lead)\uC640 \uC5C5\uBE44\uD2B8(Lag) \uAC04\uC758 \uAC00\uACA9 \uC2DC\uAC04\uCC28", bold: true }),
          new TextRun("\uB97C \uD65C\uC6A9\uD55C \uC554\uD638\uD654\uD3D0 \uD398\uC774\uD37C \uD2B8\uB808\uC774\uB529 \uC2DC\uC2A4\uD15C\uC785\uB2C8\uB2E4."),
        ]}),
        new Paragraph({ spacing: { after: 200 }, children: [
          new TextRun("\uBC14\uC774\uB09C\uC2A4\uB294 \uAE00\uB85C\uBC8C \uC2DC\uC7A5\uC758 \uC120\uD589 \uC9C0\uD45C\uB85C, \uAC00\uACA9 \uBCC0\uB3D9\uC774 \uBA3C\uC800 \uBC1C\uC0DD\uD569\uB2C8\uB2E4. \uC5C5\uBE44\uD2B8\uB294 \uD55C\uAD6D \uC2DC\uC7A5\uC758 \uD6C4\uD589 \uC9C0\uD45C\uB85C, \uC218\uCD08~\uC218\uBD84 \uB4A4\uC5D0 \uB530\uB77C\uAC11\uB2C8\uB2E4. \uC774 \uC2DC\uAC04\uCC28\uB97C \uD3EC\uCC29\uD558\uC5EC \uC5C5\uBE44\uD2B8\uC5D0\uC11C \uC120\uC81C \uB9E4\uB9E4\uD569\uB2C8\uB2E4."),
        ]}),

        // Time lag diagram
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 3120, 3120],
          rows: [
            new TableRow({ children: [
              headerCell("\uBC14\uC774\uB09C\uC2A4 \uAE09\uB4F1", 3120),
              headerCell("\uC2DC\uAC04\uCC28 (\uC218\uCD08~\uC218\uBD84)", 3120),
              headerCell("\uC5C5\uBE44\uD2B8 \uBC18\uC751", 3120),
            ]}),
            new TableRow({ children: [
              cell("$70,000 \u2192 $72,000", 3120),
              cell("\uC5C5\uBE44\uD2B8 \uC544\uC9C1 \uBBF8\uBC18\uC751", 3120, { color: "CC0000" }),
              cell("\u2192 \uC120\uC81C \uB9E4\uC218!", 3120, { bold: true, color: "006600" }),
            ]}),
            new TableRow({ children: [
              cell("\uAC00\uACA9 \uC720\uC9C0", 3120),
              cell("\uC5C5\uBE44\uD2B8 \uB530\uB77C\uC7A1\uC74C", 3120, { color: "006600" }),
              cell("\u2192 \uB9E4\uB3C4 (\uCC28\uC775 \uC2E4\uD604)", 3120, { bold: true, color: "CC0000" }),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // === 2. SYSTEM ARCHITECTURE ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. \uC2DC\uC2A4\uD15C \uC544\uD0A4\uD14D\uCC98")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 \uB370\uC774\uD130 \uC218\uC9D1 \uACC4\uCE35")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun("\uC5C5\uBE44\uD2B8\uC640 \uBC14\uC774\uB09C\uC2A4\uC758 WebSocket \uC2E4\uC2DC\uAC04 \uC2A4\uD2B8\uB9BC\uC744 \uB3D9\uC2DC \uC218\uC2E0\uD569\uB2C8\uB2E4."),
        ]}),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
          new TextRun({ text: "Upbit WebSocket: ", bold: true }), new TextRun("KRW-BTC ticker (\uCCB4\uACB0\uAC00, 24h \uAC70\uB798\uB7C9)"),
        ]}),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
          new TextRun({ text: "Binance WebSocket: ", bold: true }), new TextRun("btcusdt 24hr ticker (\uCCB4\uACB0\uAC00, \uAC70\uB798\uB7C9)"),
        ]}),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 120 }, children: [
          new TextRun({ text: "\uC790\uB3D9 \uC7AC\uC5F0\uACB0: ", bold: true }), new TextRun("\uC9C0\uC218 \uBC31\uC624\uD504 (1s \u2192 2s \u2192 4s... \uCD5C\uB300 60s)"),
        ]}),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.2 \uC2E4\uD589 \uC5D4\uC9C4 (ApiEngine)")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun("asyncio.Queue\uB85C \uB450 \uAC70\uB798\uC18C \uB370\uC774\uD130\uB97C \uD1B5\uD569\uD558\uACE0, \uB9E4 \uD2F1\uB9C8\uB2E4 \uBAA8\uB4E0 \uC804\uB7B5\uC744 \uC21C\uCC28\uC801\uC73C\uB85C \uD3C9\uAC00\uD569\uB2C8\uB2E4."),
        ]}),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.3 \uD504\uB860\uD2B8\uC5D4\uB4DC (Next.js Dashboard)")] }),
        new Paragraph({ spacing: { after: 200 }, children: [
          new TextRun("WebSocket\uC73C\uB85C \uC2E4\uC2DC\uAC04 \uB370\uC774\uD130\uB97C \uC218\uC2E0\uD558\uC5EC \uD3EC\uD2B8\uD3F4\uB9AC\uC624, \uC2DC\uC7A5 \uAC00\uACA9, \uCC28\uD2B8, \uC2DC\uADF8\uB110 \uD53C\uB4DC\uB97C \uD55C \uD654\uBA74\uC5D0 \uD45C\uC2DC\uD569\uB2C8\uB2E4."),
        ]}),

        // === 3. TRADING STRATEGIES ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. \uD2B8\uB808\uC774\uB529 \uC804\uB7B5")] }),

        // Strategy A
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.1 \uC804\uB7B5 A: LeadLag (Kimchi Premium \uC5ED\uD504\uB9AC\uBBF8\uC5C4 \uC218\uB834)")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun({ text: "\uD575\uC2EC \uC6D0\uB9AC: ", bold: true }),
          new TextRun("\uBC14\uC774\uB09C\uC2A4\uAC00 \uAE09\uB4F1\uD558\uBA74 \uAE40\uCE58\uD504\uB9AC\uBBF8\uC5C4\uC774 \uC21C\uAC04\uC801\uC73C\uB85C \uD558\uB77D(\uC5ED\uD504\uB9AC\uBBF8\uC5C4)\uD569\uB2C8\uB2E4. \uC774\uB54C \uC5C5\uBE44\uD2B8\uAC00 \uC800\uD3C9\uAC00\uB41C \uC0C1\uD0DC\uC774\uBBC0\uB85C \uB9E4\uC218\uD558\uACE0, \uD504\uB9AC\uBBF8\uC5C4\uC774 \uC815\uC0C1 \uBCF5\uADC0\uD558\uBA74 \uB9E4\uB3C4\uD569\uB2C8\uB2E4."),
        ]}),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [2340, 3510, 3510],
          rows: [
            new TableRow({ children: [
              headerCell("\uAD6C\uBD84", 2340), headerCell("\uC870\uAC74", 3510), headerCell("\uC124\uBA85", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uC9C4\uC785 (Entry)", 2340, { bold: true, color: "006600" }),
              cell("\uD504\uB9AC\uBBF8\uC5C4 \u2264 -2%", 3510),
              cell("\uC5C5\uBE44\uD2B8\uAC00 \uBC14\uC774\uB09C\uC2A4 \uB300\uBE44 \uC800\uD3C9\uAC00 \u2192 \uB9E4\uC218", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uCCAD\uC0B0 (Exit)", 2340, { bold: true, color: "CC0000" }),
              cell("\uD504\uB9AC\uBBF8\uC5C4 \u2265 +0.5%", 3510),
              cell("\uD504\uB9AC\uBBF8\uC5C4 \uC815\uC0C1 \uBCF5\uADC0 \u2192 \uCC28\uC775 \uC2E4\uD604", 3510),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 120 }, children: [] }),

        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun({ text: "\uD504\uB9AC\uBBF8\uC5C4 \uACC4\uC0B0\uC2DD: ", bold: true }),
          new TextRun("(\uC5C5\uBE44\uD2B8\uAC00 - \uBC14\uC774\uB09C\uC2A4\uAC00 \u00D7 \uD658\uC728) / (\uBC14\uC774\uB09C\uC2A4\uAC00 \u00D7 \uD658\uC728) \u00D7 100"),
        ]}),
        new Paragraph({ spacing: { after: 200 }, children: [
          new TextRun({ text: "\uD658\uC728 \uC124\uC815: ", bold: true }),
          new TextRun("\uD658\uACBD\uBCC0\uC218 FX_RATE (\uAE30\uBCF8\uAC12 1,400\uC6D0)"),
        ]}),

        // Strategy B
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.2 \uC804\uB7B5 B: Momentum Breakout (\uAC70\uB798\uB7C9 \uB3D9\uBC18 \uB3CC\uD30C)")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun({ text: "\uD575\uC2EC \uC6D0\uB9AC: ", bold: true }),
          new TextRun("\uCD5C\uADFC N\uD2F1\uC758 \uACE0\uC810\uC744 \uB3CC\uD30C\uD558\uBA74\uC11C \uD3C9\uADE0 \uAC70\uB798\uB7C9\uC758 1.5\uBC30 \uC774\uC0C1\uC774 \uB3D9\uBC18\uB420 \uB54C \uAC15\uD55C \uBAA8\uBA58\uD140\uC73C\uB85C \uD310\uB2E8\uD558\uACE0 \uC9C4\uC785\uD569\uB2C8\uB2E4."),
        ]}),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [2340, 3510, 3510],
          rows: [
            new TableRow({ children: [
              headerCell("\uAD6C\uBD84", 2340), headerCell("\uC870\uAC74", 3510), headerCell("\uC124\uBA85", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uC9C4\uC785 (Entry)", 2340, { bold: true, color: "006600" }),
              cell("\uAC00\uACA9 > \uCD5C\uADFC 5\uD2F1 \uACE0\uC810\n\uAC70\uB798\uB7C9 > \uD3C9\uADE0 \u00D7 1.5", 3510),
              cell("\uAC00\uACA9 \uB3CC\uD30C + \uAC70\uB798\uB7C9 \uAE09\uC99D \u2192 \uB9E4\uC218", 3510),
            ]}),
            new TableRow({ children: [
              cell("Trailing Stop", 2340, { bold: true, color: "CC6600" }),
              cell("\uACE0\uC810 \uB300\uBE44 1% \uD558\uB77D", 3510),
              cell("\uC9C4\uC785 \uD6C4 \uACE0\uC810 \uAC31\uC2E0, \uD558\uB77D \uC2DC \uCCAD\uC0B0", 3510),
            ]}),
            new TableRow({ children: [
              cell("Stop Loss", 2340, { bold: true, color: "CC0000" }),
              cell("\uC9C4\uC785\uAC00 \uB300\uBE44 2% \uD558\uB77D", 3510),
              cell("\uC190\uC808 \uB77C\uC778 \uB3C4\uB2EC \uC2DC \uC989\uC2DC \uCCAD\uC0B0", 3510),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // === 4. STRATEGY OPERATION ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. \uC804\uB7B5 \uC6B4\uC601 \uBC29\uC2DD")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 \uB3C5\uB9BD \uC6B4\uC601 \uAD6C\uC870")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun("\uB450 \uC804\uB7B5\uC774 "),
          new TextRun({ text: "\uB3D9\uC2DC\uC5D0 \uB3C5\uB9BD\uC801\uC73C\uB85C", bold: true }),
          new TextRun(" \uC2E4\uD589\uB429\uB2C8\uB2E4. \uAC01 \uC804\uB7B5\uC740 \uBCC4\uB3C4\uC758 \uC790\uAE08\uC744 \uD560\uB2F9\uBC1B\uC544 \uC11C\uB85C \uAC04\uC12D \uC5C6\uC774 \uC6B4\uC601\uB429\uB2C8\uB2E4."),
        ]}),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [4680, 2340, 2340],
          rows: [
            new TableRow({ children: [
              headerCell("\uC804\uB7B5", 4680), headerCell("\uD560\uB2F9 \uC790\uAE08", 2340), headerCell("\uC0C1\uD0DC", 2340),
            ]}),
            new TableRow({ children: [
              cell("LeadLag (Kimchi Premium)", 4680),
              cell("500\uB9CC\uC6D0", 2340),
              cell("\uB3C5\uB9BD \uC6B4\uC601", 2340),
            ]}),
            new TableRow({ children: [
              cell("Momentum Breakout", 4680),
              cell("500\uB9CC\uC6D0", 2340),
              cell("\uB3C5\uB9BD \uC6B4\uC601", 2340),
            ]}),
            new TableRow({ children: [
              cell("\uD569\uACC4", 4680, { bold: true }),
              cell("1,000\uB9CC\uC6D0", 2340, { bold: true }),
              cell("", 2340),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.2 \uB9E4 \uD2F1 \uC2E4\uD589 \uD750\uB984")] }),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("Upbit/Binance WebSocket\uC5D0\uC11C \uC2E4\uC2DC\uAC04 \uAC00\uACA9 \uC218\uC2E0"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("market_state \uAC31\uC2E0 (\uC5C5\uBE44\uD2B8\uAC00, \uBC14\uC774\uB09C\uC2A4\uAC00, \uAC70\uB798\uB7C9)"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("\uAC01 \uC804\uB7B5\uC5D0 on_tick() \uD638\uCD9C"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("should_enter() / should_exit() \uD3C9\uAC00"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("DailyRiskManager \uCCB4\uD06C (\uC9C4\uC785 \uC2DC)"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [
          new TextRun("\uB9E4\uB9E4 \uC2DC\uBBAC\uB808\uC774\uC158 (\uC218\uC218\uB8CC 0.05% \uC591\uBC29\uD5A5 \uC801\uC6A9)"),
        ]}),
        new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 200 }, children: [
          new TextRun("WebSocket\uC73C\uB85C \uB300\uC2DC\uBCF4\uB4DC\uC5D0 \uBE0C\uB85C\uB4DC\uCE90\uC2A4\uD2B8"),
        ]}),

        // === 5. RISK MANAGEMENT ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. \uB9AC\uC2A4\uD06C \uAD00\uB9AC")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 DailyRiskManager (\uAE00\uB85C\uBC8C \uC11C\uD0B7\uBE0C\uB808\uC774\uCEE4)")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun("\uBAA8\uB4E0 \uC804\uB7B5\uC774 \uACF5\uC720\uD558\uB294 \uB9AC\uC2A4\uD06C \uAD00\uB9AC\uC790\uB85C, \uD55C \uC804\uB7B5\uC758 \uC190\uC2E4\uC774 \uB2E4\uB978 \uC804\uB7B5\uC758 \uC2E0\uADDC \uB9E4\uB9E4\uAE4C\uC9C0 \uCC28\uB2E8\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4."),
        ]}),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 3120, 3120],
          rows: [
            new TableRow({ children: [
              headerCell("\uADDC\uCE59", 3120), headerCell("\uC784\uACC4\uAC12", 3120), headerCell("\uC791\uB3D9", 3120),
            ]}),
            new TableRow({ children: [
              cell("\uC77C\uC77C \uCD5C\uB300 \uC190\uC2E4", 3120),
              cell("50\uB9CC\uC6D0", 3120),
              cell("\uCD08\uACFC \uC2DC \uC804 \uC804\uB7B5 \uB9E4\uB9E4 \uCC28\uB2E8", 3120),
            ]}),
            new TableRow({ children: [
              cell("\uC5F0\uC18D \uC190\uC2E4 \uD69F\uC218", 3120),
              cell("5\uD68C", 3120),
              cell("\uCD08\uACFC \uC2DC \uC804 \uC804\uB7B5 \uB9E4\uB9E4 \uCC28\uB2E8", 3120),
            ]}),
            new TableRow({ children: [
              cell("\uC218\uC775 \uBC1C\uC0DD \uC2DC", 3120),
              cell("-", 3120),
              cell("\uC5F0\uC18D \uC190\uC2E4 \uCE74\uC6B4\uD2B8 \uB9AC\uC14B", 3120),
            ]}),
            new TableRow({ children: [
              cell("\uB9E4\uC77C \uB9AC\uC14B", 3120),
              cell("-", 3120),
              cell("\uC77C\uC77C \uC190\uC2E4 + \uC5F0\uC18D\uC190\uC2E4 \uCD08\uAE30\uD654", 3120),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.2 \uC804\uB7B5\uBCC4 \uC190\uC808")] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
          new TextRun({ text: "Momentum: ", bold: true }), new TextRun("Trailing Stop (1%) + Stop Loss (2%)"),
        ]}),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 200 }, children: [
          new TextRun({ text: "LeadLag: ", bold: true }), new TextRun("\uD504\uB9AC\uBBF8\uC5C4 \uAE30\uBC18 \uCCAD\uC0B0 (\uC218\uB834 \uC644\uB8CC \uC2DC)"),
        ]}),

        // === 6. FEES & SLIPPAGE ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. \uC218\uC218\uB8CC \uBC0F \uC2AC\uB9AC\uD53C\uC9C0")] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.1 \uC2E4\uC2DC\uAC04 \uD398\uC774\uD37C \uD2B8\uB808\uC774\uB529")] }),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [
          new TextRun("\uC5C5\uBE44\uD2B8 \uC218\uC218\uB8CC: 0.05% (\uB9E4\uC218/\uB9E4\uB3C4 \uC591\uBC29\uD5A5 \uC801\uC6A9)"),
        ]}),
        new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 120 }, children: [
          new TextRun("\uC2AC\uB9AC\uD53C\uC9C0: \uBBF8\uC801\uC6A9 (\uC2E4\uC2DC\uAC04\uC740 \uC2DC\uC7A5\uAC00 \uC790\uCCB4\uAC00 \uBC18\uC601)"),
        ]}),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("6.2 \uBC31\uD14C\uC2A4\uD2B8 \uC5D4\uC9C4")] }),
        new Paragraph({ spacing: { after: 120 }, children: [
          new TextRun("\uBC31\uD14C\uC2A4\uD2B8\uC5D0\uC11C\uB294 SlippageModel\uC774 3\uAC00\uC9C0 \uC694\uC18C\uB85C \uCCB4\uACB0 \uBBF8\uB044\uB7EC\uC9D0\uC744 \uCD94\uC815\uD569\uB2C8\uB2E4:"),
        ]}),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [2340, 3510, 3510],
          rows: [
            new TableRow({ children: [
              headerCell("\uC694\uC18C", 2340), headerCell("\uACC4\uC0B0", 3510), headerCell("\uC124\uBA85", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uACE0\uC815 \uC2A4\uD504\uB808\uB4DC", 2340),
              cell("\uAC00\uACA9 \u00D7 2bps", 3510),
              cell("\uD638\uAC00 \uC2A4\uD504\uB808\uB4DC \uD55C\uACC4", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uBCC0\uB3D9\uC131 \uD398\uB110\uD2F0", 2340),
              cell("\uAC00\uACA9 \u00D7 \uBCC0\uB3D9\uC131 \u00D7 \uC9C0\uC5F0(ms)", 3510),
              cell("\uC2DC\uC7A5 \uAE09\uBCC0 \uC2DC \uCCB4\uACB0 \uBBF8\uB044\uB7EC\uC9D0", 3510),
            ]}),
            new TableRow({ children: [
              cell("\uC2DC\uC7A5 \uCDA9\uACA9", 2340),
              cell("\uAC00\uACA9 \u00D7 \uACC4\uC218 \u00D7 log(1+\uC8FC\uBB38\uD06C\uAE30)", 3510),
              cell("\uB300\uB7C9 \uC8FC\uBB38 \uC2DC \uAC00\uACA9 \uC601\uD5A5", 3510),
            ]}),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        // === 7. TECH STACK ===
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("7. \uAE30\uC220 \uC2A4\uD0DD")] }),

        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [3120, 6240],
          rows: [
            new TableRow({ children: [
              headerCell("\uAD6C\uBD84", 3120), headerCell("\uAE30\uC220", 6240),
            ]}),
            new TableRow({ children: [cell("Backend", 3120, { bold: true }), cell("Python, FastAPI, uvicorn, websockets", 6240)] }),
            new TableRow({ children: [cell("Frontend", 3120, { bold: true }), cell("Next.js 16, React 19, TailwindCSS 4, lightweight-charts", 6240)] }),
            new TableRow({ children: [cell("Data Feed", 3120, { bold: true }), cell("Upbit WebSocket API, Binance WebSocket API", 6240)] }),
            new TableRow({ children: [cell("Backtest", 3120, { bold: true }), cell("pandas, numpy, SlippageModel", 6240)] }),
            new TableRow({ children: [cell("Testing", 3120, { bold: true }), cell("pytest (4 tests, all passing)", 6240)] }),
          ]
        }),
        new Paragraph({ spacing: { after: 200 }, children: [] }),

        new Paragraph({ spacing: { before: 400 }, children: [
          new TextRun({ text: "\u26A0\uFE0F \uBCF8 \uC2DC\uC2A4\uD15C\uC740 Paper Trading(\uBAA8\uC758 \uD22C\uC790) \uC804\uC6A9\uC774\uBA70, \uC2E4\uC81C \uC790\uAE08 \uAC70\uB798\uC5D0 \uC0AC\uC6A9\uB418\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.", italics: true, color: "888888" }),
        ]}),
      ]
    }
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("C:/ProjectS/latency-edge/docs/Latency_Edge_Documentation.docx", buffer);
  console.log("Document created successfully!");
});
