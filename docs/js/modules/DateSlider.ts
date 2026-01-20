/**
 * DateSlider module - Encapsulates date range slider logic.
 *
 * This module was extracted from app.ts to:
 * 1. Make slider logic testable in isolation
 * 2. Use centralized DateUtils for consistency
 * 3. Eliminate the scattered date handling that caused 8+ bugs
 * 4. Provide a clean API for initialization and updates
 */

import { parseDateUTC, toDateString, toDayIndex, fromDayIndex, DateRange, getDateRange } from './DateUtils.js';

// External library loaded via CDN script tag
declare const noUiSlider: any;

export interface DateSliderOptions {
    /**
     * Callback when slider values change
     */
    onUpdate?: (startDate: string, endDate: string) => void;

    /**
     * Callback when slider is released (for auto-filtering)
     */
    onChange?: (startDate: string, endDate: string) => void;

    /**
     * Initial start date (for persistence)
     */
    initialStartDate?: string;

    /**
     * Initial end date (for persistence)
     */
    initialEndDate?: string;
}

export class DateSlider {
    private sliderElement: HTMLElement;
    private startInput: HTMLInputElement | null;
    private endInput: HTMLInputElement | null;
    private displayElement: HTMLElement | null;
    private dateRange: DateRange | null = null;
    private isInitializing: boolean = false;
    private options: DateSliderOptions;

    constructor(
        sliderElementId: string,
        startInputId: string,
        endInputId: string,
        displayElementId: string | null = null,
        options: DateSliderOptions = {}
    ) {
        const slider = document.getElementById(sliderElementId);
        if (!slider) {
            throw new Error(`Slider element with id '${sliderElementId}' not found`);
        }

        this.sliderElement = slider;
        this.startInput = document.getElementById(startInputId) as HTMLInputElement;
        this.endInput = document.getElementById(endInputId) as HTMLInputElement;
        this.displayElement = displayElementId ? document.getElementById(displayElementId) : null;
        this.options = options;
    }

    /**
     * Initialize the slider with a date range from processing results.
     *
     * @param result - Processing result containing date range or weekly dates
     */
    initialize(result: { charts?: { date_range?: { min: string | null, max: string | null } | null, weekly?: { full_dates: string[] } | null } | null }) {
        // Extract date range from result
        let minDate: Date | null = null;
        let maxDate: Date | null = null;

        if (result.charts?.date_range?.min && result.charts?.date_range?.max) {
            // Prefer raw daily date range if available
            minDate = parseDateUTC(result.charts.date_range.min);
            maxDate = parseDateUTC(result.charts.date_range.max);
        } else if (result.charts?.weekly?.full_dates && result.charts.weekly.full_dates.length > 0) {
            // Fall back to weekly chart dates
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



        this.createSlider();
    }

    /**
     * Create or recreate the noUiSlider instance.
     */
    private createSlider() {
        if (!this.dateRange) {
            throw new Error("Cannot create slider without date range. Call initialize() first.");
        }

        // Destroy existing slider if present
        if ((this.sliderElement as any).noUiSlider) {
            (this.sliderElement as any).noUiSlider.destroy();
        }

        // Calculate initial slider positions (for persistence)
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
            // Use current input values for persistence
            const startDate = parseDateUTC(this.startInput.value);
            const endDate = parseDateUTC(this.endInput.value);

            if (startDate && endDate) {
                dayStart = Math.max(0, toDayIndex(startDate, this.dateRange.min));
                dayEnd = Math.min(this.dateRange.totalDays, toDayIndex(endDate, this.dateRange.min));
            }
        }

        // Set initialization flag to prevent auto-filter during setup
        this.isInitializing = true;

        try {
            noUiSlider.create(this.sliderElement, {
                start: [dayStart, dayEnd],
                connect: true,
                behaviour: 'drag-tap',
                range: {
                    'min': 0,
                    'max': this.dateRange.totalDays
                },
                step: 1
            });

            // Handle slider updates (while dragging)
            (this.sliderElement as any).noUiSlider.on('update', (values: any[], handle: number) => {
                const startDay = Math.round(Number(values[0]));
                const endDay = Math.round(Number(values[1]));

                const startDate = fromDayIndex(startDay, this.dateRange!.min);
                const endDate = fromDayIndex(endDay, this.dateRange!.min);

                const startDateStr = toDateString(startDate)!;
                const endDateStr = toDateString(endDate)!;

                // Update display element
                if (this.displayElement) {
                    this.displayElement.innerHTML = `${startDateStr}  —  ${endDateStr}`;
                }

                // Update hidden inputs
                if (handle === 0 && this.startInput) {
                    this.startInput.value = startDateStr;
                } else if (this.endInput) {
                    this.endInput.value = endDateStr;
                }

                // Fire onUpdate callback
                if (this.options.onUpdate && !this.isInitializing) {
                    this.options.onUpdate(startDateStr, endDateStr);
                }
            });

            // Handle slider change (when handle is released)
            (this.sliderElement as any).noUiSlider.on('change', (values: any[]) => {
                if (this.isInitializing) {
                    console.log("Slider changed during initialization. Skipping auto-action.");
                    return;
                }

                const startDay = Math.round(Number(values[0]));
                const endDay = Math.round(Number(values[1]));

                const startDate = fromDayIndex(startDay, this.dateRange!.min);
                const endDate = fromDayIndex(endDay, this.dateRange!.min);

                const startDateStr = toDateString(startDate)!;
                const endDateStr = toDateString(endDate)!;



                // Fire onChange callback
                if (this.options.onChange) {
                    this.options.onChange(startDateStr, endDateStr);
                }
            });

            // Reset initialization flag after small delay
            // This ensures all 'update' events during creation are ignored
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
    getCurrentRange(): { startDate: string, endDate: string } | null {
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
    setRange(startDate: string, endDate: string) {
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

        (this.sliderElement as any).noUiSlider.set([dayStart, dayEnd]);
    }

    /**
     * Destroy the slider instance.
     */
    destroy() {
        if ((this.sliderElement as any).noUiSlider) {
            (this.sliderElement as any).noUiSlider.destroy();
        }
        this.dateRange = null;
    }
}
