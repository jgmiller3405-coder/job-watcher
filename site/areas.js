// The metro areas the Browse page narrows to. Employers write locations in many
// ways, so each area is a pattern, matched against the location text as listed.
"use strict";

const Areas = (() => {
  // A city counts only when its state follows, so Fayetteville, NC is not Arkansas.
  const cities = (names, states) => new RegExp(`\\b(?:${names}),\\s*(?:${states})\\b(?!, Ireland)`, "i");
  const TEXAS = "TX|Texas";

  const NYC_BOROUGHS = /^(new york|new york city|manhattan|brooklyn|queens|bronx|staten island|long island city)$/i;
  // "Albany, NY, United States" names one town, which must be in the city itself.
  const NY_TOWN = /^([^,;]+), (?:NY|New York), United States$/i;

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
        "Independence|Lee'?s Summit|Blue Springs|Liberty|Gladstone|Riverside|Raytown|Grandview|Belton|Claycomo",
        "KS|MO|Kansas|Missouri").test(place),
    },
    {
      id: "chicago", name: "Chicago metro",
      test: (place) => /\bchicago\b/i.test(place) || /\bCHI\b/.test(place) || cities(
        "Mettawa|Rosemont|Schaumburg|Deerfield|Evanston|Naperville|Des Plaines|McCook|Hodgkins|Northbrook|" +
        "Lincolnshire|Vernon Hills|Waukegan|Oak Brook|Abbott Park|Libertyville|Lake Forest|Skokie|Itasca|" +
        "Downers Grove|Lisle|Aurora|Elk Grove Village|Hoffman Estates|Rolling Meadows|Arlington Heights|" +
        "Bolingbrook|Joliet|Volo",
        "IL|Illinois").test(place),
    },
    {
      id: "dallas", name: "Dallas–Fort Worth",
      test: (place) => /\bdallas\b(?!, (?:OR|GA|NC|PA)\b)/i.test(place) || /\bTX - Frisco\b|\bTX-Frisco\b/i.test(place) || cities(
        "Fort Worth|Plano|Richardson|Irving|Frisco|Addison|Allen|McKinney|Westlake|Arlington|Carrollton|" +
        "Lewisville|Southlake|Coppell|Grapevine|Farmers Branch|Garland|Grand Prairie|Roanoke|Flower Mound|The Colony",
        TEXAS).test(place),
    },
    {
      id: "nyc", name: "New York City metro",
      test: (place) => {
        if (cities("Jersey City|Hoboken", "NJ|New Jersey").test(place)) return true;
        const town = place.match(NY_TOWN);
        if (town) return NYC_BOROUGHS.test(town[1].trim());
        if (/^NY, United States$/i.test(place)) return false; // the state, with no city
        return /\bnew york\b|\bNYC\b|\bSF, SEA, NY\b/i.test(place);
      },
    },
  ];

  const byId = Object.fromEntries(list.map((area) => [area.id, area]));
  // choice: "mine" (any of the areas), one area's id, or "" (everywhere).
  const matches = (place, choice) =>
    choice === "" || (choice === "mine" ? list.some((a) => a.test(place)) : byId[choice].test(place));

  return { list, matches };
})();
