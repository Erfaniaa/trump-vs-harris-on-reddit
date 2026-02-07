# Report Generation Improvements - Implementation Plan

## Task Breakdown (2026-02-07)

### Phase 1: Critical Fixes
- [ ] Fix image rendering issues in markdown reports
- [ ] Fix table rendering (newline/character escaping for Typora)
- [ ] Filter out resolved markets (0% or 100% probability)
- [ ] Fix "Sell YES" spread strategy explanation

### Phase 2: Content Enhancements
- [ ] Expand YES/NO analysis with scenarios and interpretations
- [ ] Add entry/exit points for Silver and Ethereum
- [ ] Add long-term holding strategies (BTC, ETH, Gold, Silver)
- [ ] Emphasize "US stocks" terminology throughout
- [ ] Review and document negative PnL filter logic

### Phase 3: Strategic Additions
- [ ] Create multi-date NO betting strategy
- [ ] Add Reddit/Polymarket news integration for crypto/commodities
- [ ] Enhance cross-market smart money analysis

### Phase 4: Quality Assurance
- [ ] Check logic consistency across all reports
- [ ] Sync English and Persian reports
- [ ] Test markdown rendering in Typora
- [ ] Verify all charts display correctly

## Key Changes by File

### investment_advisor.py
- Add Silver and Ethereum entry/exit levels
- Add long-term holding strategies section
- Emphasize "US stocks" vs international

### report_generator.py
- Fix image markdown syntax (ensure proper escaping)
- Fix table rendering (escape pipes, handle newlines)
- Filter resolved markets before display
- Clarify spread trading explanations
- Add detailed YES/NO interpretations

### polymarket_fetcher.py
- Document negative PnL filter logic
- Add resolved market filtering
- Enhance comment fetching for crypto/commodities

### polymarket_betting_strategy.py
- Create multi-date NO betting strategy
- Fix spread strategy explanations
- Add more scenario-based betting

## Testing Checklist
- [ ] Test image rendering in both EN and FA reports
- [ ] Verify table rendering in Typora
- [ ] Check all mathematical formulas
- [ ] Verify cross-references work
- [ ] Test with resolved markets present
- [ ] Validate entry/exit point logic
