// The metro areas the Browse page narrows to. Employers write locations in many
// ways, so each area is a pattern, matched against the location text as listed.
"use strict";

const Areas = (() => {
  // A city counts only when its state follows, so Fayetteville, NC is not Arkansas.
  const cities = (names, states) => new RegExp(`\\b(?:${names}),\\s*(?:${states})\\b(?!, Ireland)`, "i");
  const TEXAS = "TX|Texas";

  const NYC_BOROUGHS =
    /^(new york|new york city|manhattan|brooklyn|queens|bronx|staten island|long island city|flushing|jamaica)$/i;
  // "Albany, NY, United States" or "Purchase, New York" names one town, which must
  // be in the city itself. Cities that show up in lists such as "Chicago, New York"
  // are not towns in New York State.
  const NY_TOWN = /^([^,]+), (?:NY|New York)(?:, (?:USA|United States(?: of America)?))?$/i;
  const LISTED_WITH_NY = /^(chicago|san francisco|sf|boston|seattle|atlanta|austin|london|toronto|stamford)$/i;

  // Whether one place (a part of a semicolon-separated list) is in New York City.
  function inNewYorkCity(part) {
    const town = part.match(NY_TOWN);
    if (town) return NYC_BOROUGHS.test(town[1].trim()) || LISTED_WITH_NY.test(town[1].trim());
    if (/^NY, United States$/i.test(part)) return false; // the state, with no city
    return /\bnew york\b|\bNYC\b|\bSF, SEA, NY\b/i.test(part);
  }

  const list = [
    {
      id: "nwa", name: "Northwest Arkansas",
      test: (place) => /\bnorthwest arkansas\b/i.test(place) || cities(
        "Bentonville|Rogers|Springdale|Fayetteville|Bella Vista|Lowell|Centerton|Siloam Springs",
        "AR|Arkansas").test(place),
    },
    {
      id: "kc", name: "Kansas City metro",
      test: (place) => cities(
        "Kansas City|North Kansas City|Overland Park|Olathe|Lenexa|Leawood|Shawnee|Prairie Village|Merriam|Mission|" +
        "Independence|Lee'?s Summit|Blue Springs|Liberty|Gladstone|Riverside|Raytown|Grandview|Belton|Claycomo|" +
        "New Century|Edgerton|Leavenworth",
        "KS|MO|Kansas|Missouri").test(place),
    },
    {
      id: "chicago", name: "Chicago metro",
      test: (place) => /\bchicago\b/i.test(place) || /\bCHI\b/.test(place) || cities(
        "Mettawa|Rosemont|Schaumburg|Deerfield|Evanston|Naperville|Des Plaines|McCook|Hodgkins|Northbrook|" +
        "Lincolnshire|Vernon Hills|Waukegan|Oak Brook|Abbott Park|Libertyville|Lake Forest|Skokie|Itasca|" +
        "Downers Grove|Lisle|Aurora|Elk Grove Village|Hoffman Estates|Rolling Meadows|Arlington Heights|" +
        "Bolingbrook|Joliet|Volo|Oakbrook Terrace|Franklin Park",
        "IL|Illinois").test(place),
    },
    {
      id: "dallas", name: "Dallas–Fort Worth",
      test: (place) => /\bdallas\b(?!, (?:OR|GA|NC|PA)\b)/i.test(place) || /\bTX - Frisco\b|\bTX-Frisco\b/i.test(place) || cities(
        "Fort Worth|Plano|Richardson|Irving|Frisco|Addison|Allen|McKinney|Westlake|Arlington|Carrollton|" +
        "Lewisville|Southlake|Coppell|Grapevine|Farmers Branch|Garland|Grand Prairie|Roanoke|Flower Mound|The Colony|" +
        "Mesquite|Haslet|Red Oak",
        TEXAS).test(place),
    },
    {
      id: "nyc", name: "New York City metro",
      test: (place) => cities("Jersey City|Hoboken", "NJ|New Jersey").test(place) ||
        place.split(";").some((part) => inNewYorkCity(part.trim())),
    },
  ];

  const byId = Object.fromEntries(list.map((area) => [area.id, area]));
  // choice: "mine" (any of the areas), one area's id, or "" (everywhere).
  const matches = (place, choice) =>
    choice === "" || (choice === "mine" ? list.some((a) => a.test(place)) : byId[choice].test(place));

  return { list, matches };
})();
