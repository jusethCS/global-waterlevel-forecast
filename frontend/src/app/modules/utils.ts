export class utils{

  public filterByDayWaterLevel(geojson: any, propertyKey: string) {
    return {
      type: geojson.type,
      features: geojson.features.map((feature: { properties: { [x: string]: any; hydroweb?: any; reachid?: any; basin?: any; river?: any; name?: any; latitude?: any; longitude?: any; state?: any; country?: any; datetime?: any; }; type: any; id: any; geometry: any; bbox: any; }) => {
        const { hydroweb, reachid, basin, river, name, latitude, longitude, state, country, datetime } = feature.properties;
        return {
          type: feature.type,
          id: feature.id,
          properties: {
            hydroweb,
            reachid,
            basin,
            river,
            name,
            latitude,
            longitude,
            state,
            country,
            datetime,
            alert: feature.properties[propertyKey]
          },
          geometry: feature.geometry,
          bbox: feature.bbox
        };
      })
    };
  }

  public filterByRP(geojson: any, condition: string) {
    return {
      type: geojson.type,
      features: geojson.features.filter((feature: { properties: { alert: string; }; }) => feature.properties.alert === condition)
    };
  }

  public getDateRangeGeoglows(selectedDate: Date): string[] {
    const result: string[] = [];
    const startDate = new Date(selectedDate);
    const endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 14);
    let currentDate = startDate;
    while (currentDate <= endDate) {
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, '0');
      const day = String(currentDate.getDate()).padStart(2, '0');
      result.push(`${year}-${month}-${day}`);
      currentDate.setDate(currentDate.getDate() + 1);
    }
    return result;
  }

}
