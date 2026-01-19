function parseDateUTC(dateStr) {
  if (!dateStr)
    return null;
  try {
    let date;
    if (dateStr instanceof Date) {
      date = dateStr;
    } else {
      date = new Date(dateStr);
    }
    if (isNaN(date.getTime())) {
      return null;
    }
    const utcDate = new Date(Date.UTC(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate()
    ));
    return utcDate;
  } catch (e) {
    console.error("Date parsing error:", e);
    return null;
  }
}
function toDateString(date) {
  if (!date || isNaN(date.getTime())) {
    return null;
  }
  try {
    return date.toISOString().split("T")[0];
  } catch (e) {
    console.error("Date formatting error:", e);
    return null;
  }
}
function toDayIndex(targetDate, referenceDate) {
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
  const DAY_MS = 864e5;
  const dayOffset = Math.round((targetUTC - referenceUTC) / DAY_MS);
  return dayOffset;
}
function fromDayIndex(dayIndex, referenceDate) {
  const referenceUTC = Date.UTC(
    referenceDate.getUTCFullYear(),
    referenceDate.getUTCMonth(),
    referenceDate.getUTCDate()
  );
  const DAY_MS = 864e5;
  const targetUTC = referenceUTC + dayIndex * DAY_MS;
  return new Date(targetUTC);
}
function getDateRange(dates) {
  if (!dates || dates.length === 0) {
    return null;
  }
  const parsedDates = dates.map((d) => parseDateUTC(d)).filter((d) => d !== null);
  if (parsedDates.length === 0) {
    return null;
  }
  const min = new Date(Math.min(...parsedDates.map((d) => d.getTime())));
  const max = new Date(Math.max(...parsedDates.map((d) => d.getTime())));
  const totalDays = toDayIndex(max, min);
  return { min, max, totalDays };
}
function isDateInRange(date, startDate, endDate) {
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
    const DAY_MS = 864e5;
    if (dateUTC >= endUTC + DAY_MS) {
      return false;
    }
  }
  return true;
}
function formatDate(date, format = "medium") {
  const options = {
    timeZone: "UTC"
    // Always use UTC to match our day-level precision
  };
  switch (format) {
    case "short":
      options.year = "2-digit";
      options.month = "numeric";
      options.day = "numeric";
      break;
    case "long":
      options.year = "numeric";
      options.month = "long";
      options.day = "numeric";
      break;
    case "medium":
    default:
      options.year = "numeric";
      options.month = "short";
      options.day = "numeric";
      break;
  }
  return date.toLocaleDateString("en-US", options);
}
export {
  formatDate,
  fromDayIndex,
  getDateRange,
  isDateInRange,
  parseDateUTC,
  toDateString,
  toDayIndex
};
//# sourceMappingURL=DateUtils.js.map
