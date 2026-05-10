function moveDuplicatesToSheet() {
  const sourceSheetName = 'シート1';
  const duplicateSheetName = '重複分';
  const duplicateRows = [
    6, 8, 9, 10, 37, 42, 58, 81, 83, 86, 98, 128, 133, 135, 142, 170, 174, 175,
    181, 188, 303, 320, 376, 383, 395, 397, 408, 410, 416, 418, 419, 435, 445,
    447, 449, 459, 470, 583, 607, 608, 620, 644, 649, 705, 711, 715, 752, 762,
    766, 769, 770, 783, 791, 817, 861, 863, 871, 891, 897, 900, 902, 916, 932,
    983, 1025, 1063, 1078, 1082, 1083, 1086, 1091, 1094, 1100, 1114, 1119, 1127,
    1150, 1156, 1163, 1164, 1170, 1177, 1222, 1236, 1241, 1284, 1298, 1322, 1330,
    1332, 1341, 1353, 1355, 1356, 1411, 1422, 1437, 1438, 1448, 1459, 1485, 1508,
    1515, 1528, 1596, 1598, 1609, 1632, 1722, 1756, 1791, 1847, 1852, 1927, 1928,
    2010, 2041, 2065, 2072, 2099, 2100, 2141, 2155, 2190, 2206, 2226, 2248, 2297,
    2356, 2359, 2370, 2373, 2439, 2524, 2543, 2546, 2580, 2581, 2584, 2587, 2611,
    2678, 2688, 2742, 2764, 2768, 2773, 2776, 2793, 2805, 2817, 2827, 2832, 2837,
    2838, 2845, 2872, 2893, 2907, 2908, 2919, 2920, 2941, 2944, 2960, 2975, 2981,
    2994, 3009, 3041, 3051, 3055, 3058, 3066, 3127, 3132, 3144, 3155, 3157, 3166,
    3176, 3183, 3200, 3221, 3223, 3231, 3236, 3246, 3275, 3289, 3296, 3301, 3310,
    3399, 3411, 3442, 3472, 3524, 3542, 3645, 3711, 3721, 3778, 3781, 3783, 3797,
    3801, 3809, 3815, 3961, 3968, 4128, 4380, 4397
  ];

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const source = ss.getSheetByName(sourceSheetName);
  if (!source) {
    throw new Error(`${sourceSheetName} が見つかりません。`);
  }

  let duplicate = ss.getSheetByName(duplicateSheetName);
  if (!duplicate) {
    duplicate = ss.insertSheet(duplicateSheetName);
  }

  const lastColumn = source.getLastColumn();
  if (duplicate.getLastRow() === 0) {
    source.getRange(1, 1, 1, lastColumn).copyTo(duplicate.getRange(1, 1));
  }

  const values = duplicateRows
    .slice()
    .sort((a, b) => a - b)
    .map(rowNumber => source.getRange(rowNumber, 1, 1, lastColumn).getValues()[0]);

  duplicate
    .getRange(duplicate.getLastRow() + 1, 1, values.length, lastColumn)
    .setValues(values);

  duplicateRows
    .slice()
    .sort((a, b) => b - a)
    .forEach(rowNumber => source.deleteRow(rowNumber));
}
