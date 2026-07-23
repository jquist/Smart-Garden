import { Badge } from "react-bootstrap";
import { labelForCategory, labelForRole, rolesForPlant } from "./plantLabels";

function PlantBadges({ plant, maxRoles = 3 }) {
  const roles = rolesForPlant(plant);
  const visibleRoles = roles.slice(0, maxRoles);
  const hiddenRoleCount = Math.max(roles.length - visibleRoles.length, 0);

  return (
    <div className="d-flex flex-wrap gap-1 mt-2">
      <Badge bg={plant?.plant_category === "weed" ? "danger" : "success"}>
        {labelForCategory(plant?.plant_category)}
      </Badge>

      {visibleRoles.map((role) => (
        <Badge key={role} bg="secondary">
          {labelForRole(role)}
        </Badge>
      ))}

      {hiddenRoleCount > 0 && (
        <Badge bg="light" text="dark">
          +{hiddenRoleCount}
        </Badge>
      )}
    </div>
  );
}

export default PlantBadges;
