# Battery Passport LIBSESMG17IEC — mapping notes & gap list

Product: Schneider Electric Galaxy Lithium-ion Battery Cabinet IEC, 17 x 2.04 kWh modules
(<https://www.se.com/uk/en/product/LIBSESMG17IEC/>)

Generated file: `seed/battery_passport_LIBSESMG17IEC_aas.json`
— one AAS shell + 7 submodel instances of **IDTA 02035 Digital Battery Passport** parts 1–7
(templates from `admin-shell-io/submodel-templates`, published Feb 2026), serialized per the
AAS V3.0 JSON schema (`https://admin-shell.io/aas/3/0`) from the basyx-python-sdk compliance
tool. Validates with **0 errors** against `aasJSONSchema.json`.

Data source: spreadsheet *Data attribute longlist_v1.2* (Battery Pass consortium longlist,
Jan 2025) with sample values for the Galaxy LiB. Row numbers below refer to the `#` column.

All semanticIds are taken verbatim from the official IDTA 02035 template JSON files —
none were invented. Unknown **values** are marked in-line with the literal prefix `TODO:`.

---

## (a) Spreadsheet fields with no clear IDTA-02035 mapping

| Row | Attribute | Why unmapped |
|---|---|---|
| 14 | Carbon footprint label | No value in spreadsheet; no dedicated element in Part 3 (the label class maps to `PerformanceClass`, kept as TODO from row 24) |
| 16 | Meaning of labels and symbols | "YES" only — captured as part of the user-manual Document in Part 2; no dedicated element |
| 26 | General battery and manufacturer information (CF section) | Value "Samsung LIBSMG95MODA" (module vendor) — no element in Part 3; module-level info is out of scope of the cabinet-level passport |
| 28 | Information of due diligence report | **No IDTA-02035 part covers supply chain due diligence** (parts are: nameplate, documentation, PCF, technical data, condition, materials, circularity). Would have to be attached as a Part 2 Document; value is "?" anyway |
| 29 | Third party assurances of recognised schemes | Same — no due-diligence submodel; no value |
| 30 | Supply chain indices | Same — no due-diligence submodel; no value |
| 84 | Temperature information "18–28 degC" (recommended operating range) | Part 4 `Temperature` only has *idle-state* boundaries (rows 85/86, mapped); Part 5 `TemperatureInformation` only has time-in-extreme counters (rows 87–90, mapped). No element for a recommended operating range |

## (b) Required IDTA-02035 elements with no data in the spreadsheet (marked `TODO:` in the JSON)

| Element (part) | Spreadsheet situation |
|---|---|
| `ManufacturerIdentifier` (P1, P4) | Row 4 gives name/address only, no identifier code |
| `UniqueFacilityIdentifier` (P1) | Row 5 gives "Philippines" / Cavite plant address, no formal UFI |
| `EUDeclarationOfConformity` → DocumentIdentifier (P1) | Row 17 = "YES", no document identifier |
| `ResultsOfTestReportsProvingCompliance` → DocumentIdentifier (P1) | Row 18 = "YES with IEC/UL certificates", no identifiers |
| `PcfCalculationMethods`, `ReferenceImpactUnitForCalculation`, `QuantityOfMeasureForCalculation` (P3) | Not in spreadsheet; PEP study (ENVPEP2104006_EN) referenced but methodology fields not extracted |
| `PerformanceClass` (P3) | Row 24 = "?" |
| `RatedCapacity` (P4) | Row 52 gives a brochure URL + "2.04 kWh" (per module); no Ah figure (declared unit is Ah) |
| `InitialRoundTripEnergyEfficiency`, `RoundTripEnergyEfficiencyAt50PercentOfCycleLife` (P4) | Rows 67/68 = "no" |
| `InitialInternalResistanceAtBatteryCellLevel` (P4) | Row 74 gives 3.480 mΩ for "cell and pack" — assigned to pack level (0.00348 Ω); cell level left TODO |
| `OriginalPowerCapability.atSoc` (P4), `RemainingPowerCapability.AtSoC` (P5) | Rows 62/63 give 184 kW without a SoC reference |
| `ExpectedNumberOfCycles` (P4), `NumberOfFullCyclesValue` (P5) | Rows 77/78 give a usage profile ("2 cycles 100% DOD + 24 cycles 5% DOD"), not a single integer |
| `cycleLifeReferenceTest` (P4) | Row 79 = "?" |
| `RemainingCapacityValue` (P5) | Row 53 = "1.5 kWh or 80% SOH" — not convertible to the expected Ah figure |
| All `LastUpdate` timestamps (P5) | Telemetry timestamps not in spreadsheet (data kit optional from Q3-2025) |
| `BatteryMaterials`, `HazardousSubstances` details (P6) | Rows 32–35 = "YES in MSDS (see attached file)" — the MSDS itself was not provided, so per-material name/mass/CRM-flag and per-substance class/concentration are TODO placeholders |
| Spare part supplier address/email, part names/numbers (P7) | Rows 37/38 = "yes in user manual" / "yes from SE" — supplier set to Schneider Electric + se.com, details TODO |
| `SafetyInstructions`, `SeparateCollection`, `InformationOnCollection` document identifiers (P7) | Rows 39/12/51 reference the MSDS / label / "attached file" without identifiers |

## Derived values (flagged, not straight from a cell)

- `WarrantyPeriod` = `2027-11` (xs:gYearMonth): manufacture 2024-11 (row 6) + 3 years (row 8).
- `PowerFade` = 0, `InternalResistanceIncreaseAtBatteryPackLevel` = 0: source value "NO"/"no" read as "no fade/increase".
- Times in extreme temperatures converted to **minutes** (declared spreadsheet unit): 2903.1 / 348.15 / 130.05 / 20.73.
- Power values stored in **W** (spreadsheet unit column): 184 kW → 184000, 231 kW → 231000.
- `ClearName` for chemistry expands the row-31 acronyms "LMO + NCM".
- `InformationOnAccidents` (row 93 = "no") serialized as the SML with no `value` (no accident documents).
- Row 50 URL (end-user role) mapped to `EndOfLifeInformation/WastePrevention`; the same manual URL serves `DismantlingAndRemovalInformation` (row 36).
- Rows 40–48: four `RecycledContent` entries (Ni/Co/Li/Pb) with pre/post-consumer share 0; `RenewableContent` 0.
- Rows 19–23: four `ProductCarbonFootprint` entries — total 13258 kgCO2eq plus one per lifecycle phase (10900 production / 101 distribution / 1010 end-of-life). Row 20 (raw-material contribution) is "NA" in the source and is noted in the total's phase list.

## Likely blockers for BatteryPass-Ready (batterypass-ready.gefeg.com) validation

1. **`TODO:` strings inside typed values** — every mandatory element kept its template `valueType`
   (xs:float, xs:date, xs:gYearMonth, xs:dateTime, xs:unsignedInt…). The generic AAS JSON schema does
   not check value lexical space, but a value-level validator will reject e.g.
   `RatedCapacity = "TODO: …"` against xs:float. Every such case is listed in section (b) above.
2. **Enumerated vocabularies not confirmed**: `BatteryCategory` ("stationary ESS"), `LifeCycleStage`
   ("Original"), `LifeCyclePhase` names, and `ExtinguishingAgent` ("No") were carried over verbatim
   from the spreadsheet; the test environment may expect a fixed code list.
3. **Battery passport identifier**: row 1 value `LIBSESMG17IEC` is a *model* reference, but the
   passport identifier must be unique per individual battery. It is carried as a
   `specificAssetId` on the shell; the serialized unique id used throughout is
   `LIBSESMG17IEC-QS24445-128` (row 2).
4. **StateOfCharge** stored as `0.8` exactly as in the source — confirm whether the test
   environment expects a percentage (80).
5. Document classification `ClassificationSystem`/`ClassId` in Part 2 are TODO (no VDI 2770 class
   codes were assumed).
