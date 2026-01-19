function isProcessingResult(output) {
  return output.success === true;
}
function isErrorResponse(output) {
  return output.success === false;
}
export {
  isErrorResponse,
  isProcessingResult
};
//# sourceMappingURL=index.js.map
