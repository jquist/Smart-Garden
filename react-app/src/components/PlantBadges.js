import { Badge } from "react-bootstrap";
import { labelForCategory, labelForRole, rolesForPlant } from "./plantLabels";

function PlantBadges({ plant, maxRoles = 3 }) {
  const roles = rolesForPlant(plant);
  const visibleRoles = roles.slice(0, maxRoles);
  const hiddenRoleCount = Math.max(roles.length - visibleRoles.length, 0);
  const isWeed = plant?.plant_category === "weed";

  return (
    <div className="plant-badges">
      <Badge bg="light" className={`plant-badge ${isWeed ? "plant-badge-weed" : "plant-badge-category"}`}>
        {labelForCategory(plant?.plant_category)}
      </Badge>

      {visibleRoles.map((role) => (
        <Badge key={role} bg="light" className="plant-badge plant-badge-role">
          {labelForRole(role)}
        </Badge>
      ))}

      {hiddenRoleCount > 0 && (
        <Badge bg="light" className="plant-badge plant-badge-more">
          +{hiddenRoleCount}
        </Badge>
      )}
    </div>
  );
}

export default PlantBadges;
