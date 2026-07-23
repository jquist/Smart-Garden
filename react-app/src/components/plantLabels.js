export const CATEGORY_LABELS = {
  cover_crop: "Cover crop",
  flower: "Flower",
  fruit: "Fruit",
  herb: "Herb",
  ornamental: "Ornamental",
  tree_shrub: "Tree or shrub",
  vegetable: "Vegetable",
  weed: "Weed / problem plant",
  wildlife_native: "Wildlife / native",
};

export const CATEGORY_OPTIONS = [
  { value: "", label: "All plants" },
  { value: "vegetable", label: "Vegetables" },
  { value: "herb", label: "Herbs" },
  { value: "fruit", label: "Fruit" },
  { value: "flower", label: "Flowers" },
  { value: "cover_crop", label: "Cover crops" },
  { value: "wildlife_native", label: "Wildlife / native" },
  { value: "tree_shrub", label: "Trees / shrubs" },
  { value: "ornamental", label: "Ornamentals" },
  { value: "weed", label: "Weeds / problem plants" },
];

export const ROLE_LABELS = {
  aromatic_pest_confuser: "Aromatic",
  beneficial_insect_plant: "Beneficial insects",
  creeping_perennial: "Creeping perennial",
  cover_crop: "Cover crop",
  deep_rooted_perennial: "Deep-rooted",
  edible: "Edible",
  flowering: "Flowering",
  green_manure: "Green manure",
  ground_cover: "Ground cover",
  hedgerow: "Hedgerow",
  invasive: "Invasive",
  living_mulch: "Living mulch",
  nitrogen_fixer: "Nitrogen fixer",
  ornamental: "Ornamental",
  perennial_plant: "Perennial",
  pollinator: "Pollinator",
  problem_plant: "Problem plant",
  seeding_annual: "Self-seeding",
  shrub: "Shrub",
  soil_improver: "Soil improver",
  trap_crop: "Trap crop",
  tree: "Tree",
  toxic: "Toxic",
  weed: "Weed",
  weed_suppressor: "Weed suppressor",
  wildlife_support: "Wildlife support",
};

export function labelForCategory(category) {
  return CATEGORY_LABELS[category] || "Unlabelled";
}

export function labelForRole(role) {
  return ROLE_LABELS[role] || String(role || "").replace(/_/g, " ");
}

export function rolesForPlant(plant) {
  return Array.isArray(plant?.plant_roles) ? plant.plant_roles : [];
}
