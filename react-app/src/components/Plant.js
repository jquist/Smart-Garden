import { Card } from "react-bootstrap";
import { Link } from "react-router-dom";
import PlantBadges from "./PlantBadges";

function Plant({ data,disableLink }) {
  if (disableLink) 
      return (
        <Card className="plant-card">
          <Card.Body className="plant-card-body">
            <Card.Title>{data.name}</Card.Title>
            <PlantBadges plant={data} />
          </Card.Body>
        </Card>
      );
  return (
    <Link to={`/plant/${data.id}`} className="plant-link">
      <Card className="plant-card">
        <Card.Body className="plant-card-body">
          <Card.Title>{data.name}</Card.Title>
          <PlantBadges plant={data} />
        </Card.Body>
      </Card>
    </Link>
  );
}

export default Plant;
