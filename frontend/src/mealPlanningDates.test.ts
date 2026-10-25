import { describe, expect, it } from "vitest";
import {
  addCalendarDays,
  annualMaximumEndDate,
  parseCalendarDate,
  shiftMonthClamped,
  visibleDateRange,
} from "./mealPlanningDates";

describe("meal-planning date arithmetic", () => {
  it("keeps calendar dates local when adding days across month and year boundaries", () => {
    expect(addCalendarDays("2026-12-31", 1)).toBe("2027-01-01");
    expect(addCalendarDays("2027-03-28", 1)).toBe("2027-03-29");
  });

  it("starts the weekly view on Monday and contains exactly seven days", () => {
    const range = visibleDateRange("2026-11-04", "week");
    expect(range.start).toBe("2026-11-02");
    expect(range.end).toBe("2026-11-08");
    expect(range.dates).toHaveLength(7);
  });

  it("builds a Monday-first month grid containing the entire month", () => {
    const range = visibleDateRange("2026-11-15", "month");
    expect(range.start).toBe("2026-10-26");
    expect(range.end).toBe("2026-12-06");
    expect(range.dates).toContain("2026-11-01");
    expect(range.dates).toContain("2026-11-30");
  });

  it("clamps month navigation to the destination month's last day", () => {
    expect(shiftMonthClamped("2026-01-31", 1)).toBe("2026-02-28");
    expect(shiftMonthClamped("2028-01-31", 1)).toBe("2028-02-29");
    expect(shiftMonthClamped("2026-03-31", -1)).toBe("2026-02-28");
  });

  it("uses the confirmed annual boundary, including leap-day starts", () => {
    expect(annualMaximumEndDate("2026-11-02")).toBe("2027-11-01");
    expect(annualMaximumEndDate("2028-02-29")).toBe("2029-02-28");
  });

  it("rejects invalid dates instead of allowing JavaScript date rollover", () => {
    expect(() => parseCalendarDate("2026-02-30")).toThrow("Invalid calendar date");
  });
});
