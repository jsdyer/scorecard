# Policy Rate Scorecard

[Open Policy Rate Scorecard](https://coolcode.ca/scorecard/) · [Download the complete dataset](https://coolcode.ca/scorecard/data/scorecard.json) · [BankRate Lab](https://coolcode.ca/bankrates/)

Compare the interest rate that Canadian market participants expected with the target for the overnight rate the Bank of Canada eventually announced.

<!-- coolcode:guide -->
Pick a decision month to see the eligible survey medians, respondent counts and middle halves of responses. Switch to the last public forecast per decision to see how often it matched and the average size of a miss. Download either view as CSV.
<!-- /coolcode:guide -->

## Coverage and method

- Quarterly Market Participants Survey releases from 2025 Q1 onward. The initial set covers decisions from June 2025, the earliest entry in the Bank’s recent decisions table at collection. Each Thursday a collector re-reads the survey archive and updates the saved decisions. Retrieval is dated in UTC.
- Only individually named months in policy interest rate question 2.1 enter the tool. Rows for calendar quarters and longer horizons have different meanings. Eligible releases must be public strictly before the relevant decision day. A same-month forecast with no verified decision date stays out until eligibility can be established.
- Each receipt includes the edition and publication date, survey URL, target month, lower quartile, median, upper quartile, respondent count, decision date and announced target. Pending outcomes have null dates and values. Percentage rates use published precision.
- The actual is the announced target rate from the Bank’s dated decision table, including unchanged decisions. Its date is the announcement date. Changes generally become effective one day later.
- Signed error in basis points is 100 times (median minus actual). The overall view picks the last public edition for each completed decision, so repeated forecasts cannot give one meeting extra weight.
- The collector validates the source headings and quarterly sequence. An ambiguous decision month or a lost historical result fails the refresh and retains the previous snapshot.

## Sources and reuse

Source: Bank of Canada. CoolCode selected, reformatted and matched two sources. The Bank’s [Market Participants Survey archive](https://www.bankofcanada.ca/content_type/publications/market-participants-survey/) links individual source tables. The [policy interest rate](https://www.bankofcanada.ca/core-functions/monetary-policy/key-interest-rate/) page lists dated decisions. [Bank of Canada terms](https://www.bankofcanada.ca/terms/) apply to Bank material. CoolCode is independent of the Bank.

## Run

Use Python 3.12 and a recent Node version. Run `python scripts/refresh.py` to update the checked-in dataset through public HTTPS endpoints. Run `node --test tests/*.test.mjs`, `python -m unittest discover -s tests -v` and `python scripts/build.py`. Serve `dist/` with any static HTTP server. The built site works from its project subpath. Selecting a month and exporting CSV take place in the browser.

GitHub Actions runs the source refresh weekly with a manual trigger, commits a verified snapshot and triggers the Pages workflow. The Pages workflow validates a build offline and exercises navigation and export in Chromium before deployment.
