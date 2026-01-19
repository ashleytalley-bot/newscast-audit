import { parseDateUTC, toDateString, toDayIndex, fromDayIndex, getDateRange } from "./DateUtils.js";
class DateSlider {
  constructor(sliderElementId, startInputId, endInputId, displayElementId = null, options = {}) {
    this.dateRange = null;
    this.isInitializing = false;
    const slider = document.getElementById(sliderElementId);
    if (!slider) {
      throw new Error(`Slider element with id '${sliderElementId}' not found`);
    }
    this.sliderElement = slider;
    this.startInput = document.getElementById(startInputId);
    this.endInput = document.getElementById(endInputId);
    this.displayElement = displayElementId ? document.getElementById(displayElementId) : null;
    this.options = options;
  }
  /**
   * Initialize the slider with a date range from processing results.
   *
   * @param result - Processing result containing date range or weekly dates
   */
  initialize(result) {
    let minDate = null;
    let maxDate = null;
    if (result.charts?.date_range?.min && result.charts?.date_range?.max) {
      minDate = parseDateUTC(result.charts.date_range.min);
      maxDate = parseDateUTC(result.charts.date_range.max);
      console.log("Using raw daily date range:", result.charts.date_range);
    } else if (result.charts?.weekly?.full_dates && result.charts.weekly.full_dates.length > 0) {
      const dateRange = getDateRange(result.charts.weekly.full_dates);
      if (dateRange) {
        minDate = dateRange.min;
        maxDate = dateRange.max;
      }
    }
    if (!minDate || !maxDate) {
      console.warn("No valid date range found in result. Slider not initialized.");
      return;
    }
    this.dateRange = {
      min: minDate,
      max: maxDate,
      totalDays: toDayIndex(maxDate, minDate)
    };
    console.log("Slider Setup (UTC):", {
      minDateStr: toDateString(this.dateRange.min),
      maxDateStr: toDateString(this.dateRange.max),
      totalDays: this.dateRange.totalDays
    });
    this.createSlider();
  }
  /**
   * Create or recreate the noUiSlider instance.
   */
  createSlider() {
    if (!this.dateRange) {
      throw new Error("Cannot create slider without date range. Call initialize() first.");
    }
    if (this.sliderElement.noUiSlider) {
      this.sliderElement.noUiSlider.destroy();
    }
    let dayStart = 0;
    let dayEnd = this.dateRange.totalDays;
    if (this.options.initialStartDate && this.options.initialEndDate) {
      const startDate = parseDateUTC(this.options.initialStartDate);
      const endDate = parseDateUTC(this.options.initialEndDate);
      if (startDate && endDate) {
        dayStart = Math.max(0, toDayIndex(startDate, this.dateRange.min));
        dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(endDate, this.dateRange.min));
      }
    } else if (this.startInput?.value && this.endInput?.value) {
      const startDate = parseDateUTC(this.startInput.value);
      const endDate = parseDateUTC(this.endInput.value);
      if (startDate && endDate) {
        dayStart = Math.max(0, toDayIndex(startDate, this.dateRange.min));
        dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(endDate, this.dateRange.min));
      }
    }
    this.isInitializing = true;
    try {
      noUiSlider.create(this.sliderElement, {
        start: [dayStart, dayEnd],
        connect: true,
        behaviour: "drag-tap",
        range: {
          "min": 0,
          "max": this.dateRange.totalDays
        },
        step: 1
      });
      this.sliderElement.noUiSlider.on("update", (values, handle) => {
        const startDay = Math.round(Number(values[0]));
        const endDay = Math.round(Number(values[1]));
        const startDate = fromDayIndex(startDay, this.dateRange.min);
        const endDate = fromDayIndex(endDay, this.dateRange.min);
        const startDateStr = toDateString(startDate);
        const endDateStr = toDateString(endDate);
        if (this.displayElement) {
          this.displayElement.innerHTML = `${startDateStr}  \u2014  ${endDateStr}`;
        }
        if (handle === 0 && this.startInput) {
          this.startInput.value = startDateStr;
        } else if (this.endInput) {
          this.endInput.value = endDateStr;
        }
        if (this.options.onUpdate && !this.isInitializing) {
          this.options.onUpdate(startDateStr, endDateStr);
        }
      });
      this.sliderElement.noUiSlider.on("change", (values) => {
        if (this.isInitializing) {
          console.log("Slider changed during initialization. Skipping auto-action.");
          return;
        }
        const startDay = Math.round(Number(values[0]));
        const endDay = Math.round(Number(values[1]));
        const startDate = fromDayIndex(startDay, this.dateRange.min);
        const endDate = fromDayIndex(endDay, this.dateRange.min);
        const startDateStr = toDateString(startDate);
        const endDateStr = toDateString(endDate);
        console.log("Slider released. Triggering onChange callback...");
        if (this.options.onChange) {
          this.options.onChange(startDateStr, endDateStr);
        }
      });
      setTimeout(() => {
        this.isInitializing = false;
        console.log("Slider initialization complete.");
      }, 100);
    } catch (err) {
      console.error("Slider creation failed:", err);
      this.isInitializing = false;
      throw err;
    }
  }
  /**
   * Get the current date range from the slider.
   */
  getCurrentRange() {
    if (!this.startInput || !this.endInput) {
      return null;
    }
    return {
      startDate: this.startInput.value,
      endDate: this.endInput.value
    };
  }
  /**
   * Programmatically set the slider range.
   */
  setRange(startDate, endDate) {
    if (!this.dateRange) {
      throw new Error("Slider not initialized");
    }
    const start = parseDateUTC(startDate);
    const end = parseDateUTC(endDate);
    if (!start || !end) {
      throw new Error("Invalid date strings provided");
    }
    const dayStart = Math.max(0, toDayIndex(start, this.dateRange.min));
    const dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(end, this.dateRange.min));
    this.sliderElement.noUiSlider.set([dayStart, dayEnd]);
  }
  /**
   * Destroy the slider instance.
   */
  destroy() {
    if (this.sliderElement.noUiSlider) {
      this.sliderElement.noUiSlider.destroy();
    }
    this.dateRange = null;
  }
}
export {
  DateSlider
};
//# sourceMappingURL=DateSlider.js.map
