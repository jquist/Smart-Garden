import { Card } from "react-bootstrap";
import { Link } from "react-router-dom";
import PlantBadges from "./PlantBadges";

function descriptionText(data) {
  return data?.description || data?.planting_tips || "Open this plant for spacing, timing, companion notes, and planting guidance.";
}

function Plant({ data,disableLink }) {
  if (disableLink) 
      return (
        <Card className="plant-card">
          <Card.Body className="plant-card-body">
            <Card.Title>{data.name}</Card.Title>
            <PlantBadges plant={data} />
            <Card.Text className="plant-card-description">
              {descriptionText(data)}
            </Card.Text>
          </Card.Body>
        </Card>
      );
  return (
    <Link to={`/plant/${data.id}`} className="plant-link">
      <Card className="plant-card">
        <Card.Body className="plant-card-body">
          <Card.Title>{data.name}</Card.Title>
          <PlantBadges plant={data} />
          <Card.Text className="plant-card-description">
            {descriptionText(data)}
          </Card.Text>
        </Card.Body>
      </Card>
    </Link>
  );
}

export default Plant;
