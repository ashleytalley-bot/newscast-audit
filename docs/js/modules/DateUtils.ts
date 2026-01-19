/**
 * Shared date utilities for consistent frontend date handling.
 *
 * This module mirrors the Python datetime_utils.py to ensure consistent
 * date handling between backend and frontend. Key principles:
 *
 * 1. All dates operate at day-level granularity (no time components)
 * 2. UTC math is used to avoid DST/timezone shifts
 * 3. Day-index representation for slider (avoids floating-point precision issues)
 * 4. Inclusive end dates (fixes 1/16 clipping bug)
 */

/**
 * Parse a date string into a UTC midnight Date object.
 *
 * This ensures all dates are normalized to day-level precision at UTC midnight,
 * avoiding timezone shifts and DST complications.
 *
 * @param dateStr - ISO date string (YYYY-MM-DD) or Date object
 * @returns UTC Date object at midnight, or null if invalid
 *
 * @example
 * parseDateUTC("2024-01-15") // Date representing 2024-01-15 00:00:00 UTC
 */
export function parseDateUTC(dateStr: string | Date | null): Date | null {
    if (!dateStr) return null;

    try {
        let date: Date;

        if (dateStr instanceof Date) {
            date = dateStr;
        } else {
            // Parse string as Date
            date = new Date(dateStr);
        }

        if (isNaN(date.getTime())) {
            return null;
        }

        // Convert to UTC midnight (day-level precision)
        const utcDate = new Date(Date.UTC(
            date.getUTCFullYear(),
            date.getUTCMonth(),
            date.getUTCDate()
        ));

        return utcDate;
    } catch (e) {
        console.error('Date parsing error:', e);
        return null;
    }
}

/**
 * Convert a date to ISO string format (YYYY-MM-DD).
 *
 * @param date - Date object
 * @returns ISO date string or null if invalid
 *
 * @example
 * toDateString(new Date("2024-01-15")) // "2024-01-15"
 */
export function toDateString(date: Date | null): string | null {
    if (!date || isNaN(date.getTime())) {
        return null;
    }

    try {
        return date.toISOString().split('T')[0];
    } catch (e) {
        console.error('Date formatting error:', e);
        return null;
    }
}

/**
 * Calculate the day index (offset from a reference date).
 *
 * This is the core function for the date slider, converting dates to
 * integer day indices to avoid floating-point precision issues.
 *
 * @param targetDate - The date to calculate offset for
 * @param referenceDate - The reference date (usually min date)
 * @returns Number of days from reference (0-based)
 *
 * @example
 * toDayIndex(new Date("2024-01-05"), new Date("2024-01-01")) // 4
 */
export function toDayIndex(targetDate: Date, referenceDate: Date): number {
    const targetUTC = Date.UTC(
        targetDate.getUTCFullYear(),
        targetDate.getUTCMonth(),
        targetDate.getUTCDate()
    );

    const referenceUTC = Date.UTC(
        referenceDate.getUTCFullYear(),
        referenceDate.getUTCMonth(),
        referenceDate.getUTCDate()
    );

    const DAY_MS = 86400000; // 24 * 60 * 60 * 1000
    const dayOffset = Math.round((targetUTC - referenceUTC) / DAY_MS);

    return dayOffset;
}

/**
 * Convert a day index back to a Date object.
 *
 * @param dayIndex - Day offset from reference date (0-based)
 * @param referenceDate - The reference date
 * @returns Date object at UTC midnight
 *
 * @example
 * fromDayIndex(4, new Date("2024-01-01")) // Date("2024-01-05")
 */
export function fromDayIndex(dayIndex: number, referenceDate: Date): Date {
    const referenceUTC = Date.UTC(
        referenceDate.getUTCFullYear(),
        referenceDate.getUTCMonth(),
        referenceDate.getUTCDate()
    );

    const DAY_MS = 86400000;
    const targetUTC = referenceUTC + (dayIndex * DAY_MS);

    return new Date(targetUTC);
}

/**
 * Get the date range (min/max) from an array of date strings.
 *
 * @param dates - Array of ISO date strings
 * @returns Object with min and max dates, or null if empty
 */
export interface DateRange {
    min: Date;
    max: Date;
    totalDays: number;
}

export function getDateRange(dates: string[]): DateRange | null {
    if (!dates || dates.length === 0) {
        return null;
    }

    const parsedDates = dates
        .map(d => parseDateUTC(d))
        .filter(d => d !== null) as Date[];

    if (parsedDates.length === 0) {
        return null;
    }

    const min = new Date(Math.min(...parsedDates.map(d => d.getTime())));
    const max = new Date(Math.max(...parsedDates.map(d => d.getTime())));

    const totalDays = toDayIndex(max, min);

    return { min, max, totalDays };
}

/**
 * Check if a date falls within a range (inclusive of both start and end).
 *
 * This implements the same inclusive logic as the Python filter_by_date_range.
 *
 * @param date - Date to check
 * @param startDate - Range start (inclusive)
 * @param endDate - Range end (inclusive - entire day included)
 * @returns True if date is within range
 */
export function isDateInRange(
    date: Date,
    startDate: Date | null,
    endDate: Date | null
): boolean {
    const dateUTC = Date.UTC(
        date.getUTCFullYear(),
        date.getUTCMonth(),
        date.getUTCDate()
    );

    if (startDate) {
        const startUTC = Date.UTC(
            startDate.getUTCFullYear(),
            startDate.getUTCMonth(),
            startDate.getUTCDate()
        );
        if (dateUTC < startUTC) {
            return false;
        }
    }

    if (endDate) {
        const endUTC = Date.UTC(
            endDate.getUTCFullYear(),
            endDate.getUTCMonth(),
            endDate.getUTCDate()
        );
        // Add 1 day to make end date inclusive (same as Python implementation)
        const DAY_MS = 86400000;
        if (dateUTC >= endUTC + DAY_MS) {
            return false;
        }
    }

    return true;
}

/**
 * Format a date for display (locale-aware).
 *
 * @param date - Date object
 * @param format - Format style ('short' | 'medium' | 'long')
 * @returns Formatted date string
 *
 * @example
 * formatDate(new Date("2024-01-15"), 'short') // "1/15/24"
 * formatDate(new Date("2024-01-15"), 'medium') // "Jan 15, 2024"
 */
export function formatDate(
    date: Date,
    format: 'short' | 'medium' | 'long' = 'medium'
): string {
    const options: Intl.DateTimeFormatOptions = {
        timeZone: 'UTC', // Always use UTC to match our day-level precision
    };

    switch (format) {
        case 'short':
            options.year = '2-digit';
            options.month = 'numeric';
            options.day = 'numeric';
            break;
        case 'long':
            options.year = 'numeric';
            options.month = 'long';
            options.day = 'numeric';
            break;
        case 'medium':
        default:
            options.year = 'numeric';
            options.month = 'short';
            options.day = 'numeric';
            break;
    }

    return date.toLocaleDateString('en-US', options);
}
