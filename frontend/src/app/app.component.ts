// TS MODULES AND LIBRARIES
import { CommonModule } from '@angular/common';
import { Component, ElementRef, Renderer2, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule, MatLabel } from '@angular/material/form-field';
import { MatSelect, MatOption } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { FormControl, FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { provideMomentDateAdapter } from '@angular/material-moment-adapter';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ChangeDetectorRef } from '@angular/core';

// JS LIBRARIES
import * as L from 'leaflet';
import * as esri from "esri-leaflet";
import * as PlotlyJS from 'plotly.js-dist-min';
import html2canvas from 'html2canvas';
import { PlotlyModule } from 'angular-plotly.js';
PlotlyModule.plotlyjs = PlotlyJS;

// CUSTOM COMPONENTS AND MODULES
import { AppTemplateComponent } from './components/template/app-template.component';
import { MatInputModule } from '@angular/material/input';
import { utils } from './modules/utils';
import { environment } from '../environments/environment';
import { DropdownComponent } from "./components/dropdown/dropdown.component";
import { providers } from './modules/providers';
import { LoadingComponent } from "./components/loading/loading.component";


// Definimos una interfaz para la configuración de cada capa
interface FloodLayerConfig {
  condition: string;
  isActive: boolean;
  layerKey: keyof FloodLayers;
}

// Creamos un tipo para agrupar las capas en un objeto
interface FloodLayers {
  [key: string]: L.GeoJSON | null;
}


@Component({
  selector: 'app-root',
  standalone: true,
  providers: [provideMomentDateAdapter(new providers().dateFormat)],
  imports: [
    AppTemplateComponent,
    CommonModule,
    MatButtonModule,
    MatFormFieldModule,
    MatDatepickerModule,
    FormsModule,
    ReactiveFormsModule,
    MatSlideToggleModule,
    PlotlyModule,
    MatInputModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatAutocompleteModule,
    ReactiveFormsModule,
    DropdownComponent,
    LoadingComponent
],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {

  // Variables
  public map!: L.Map;
  public isPlay:boolean = false;
  public utilsApp = new utils();

  @ViewChild('template') template!: AppTemplateComponent;
  @ViewChild('panelPlot') panelPlot!: ElementRef;
  @ViewChild('table') table!: ElementRef;

  // Date Input
  public dateControl = new FormControl(new Date());
  public dateControlPanel = new FormControl(new Date());
  public minDate = new Date('2025-01-01');
  public maxDate = new Date();
  public rangeDate:string[] = [];

  // Metadata¿
  public basin: string = "";
  public country: string = "";
  public hydroweb: string = "";
  public latitude: string = "";
  public longitude: string = "";
  public name: string = "";
  public reachid: string = "";
  public river: string = "";
  public state: string = "";


  // Flood warnings
  public isActiveFlood000:boolean = false;
  public isActiveFlood002:boolean = true;
  public isActiveFlood005:boolean = true;
  public isActiveFlood010:boolean = true;
  public isActiveFlood025:boolean = true;
  public isActiveFlood050:boolean = true;
  public isActiveFlood100:boolean = true;
  public activeDateIndex:number = 0;
  public geoglowsFloodWarnings:any;
  public geoglowsFloodWarningsDownload:any;
  public geoglowsFlood000:any;
  public geoglowsFlood002:any;
  public geoglowsFlood005:any;
  public geoglowsFlood010:any;
  public geoglowsFlood025:any;
  public geoglowsFlood050:any;
  public geoglowsFlood100:any;
  public legendControl = new L.Control({position: 'bottomleft'});

  // Plots
  public historicalSimulationPlot: any;
  public dailyAveragePlot:any;
  public monthlyAveragePlot:any;
  public flowDurationCurve:any;
  public volumePlot:any;
  public forecastPlot:any;
  public isReadyDataPlot:boolean = false;
  public htmlContent:string = "";
  //public metricTable:string = "";
  public metricTable: SafeHtml | undefined;

  public intervalId: any;



  constructor(
    private renderer: Renderer2,
    private sanitizer: DomSanitizer,
    private cd: ChangeDetectorRef) {}


  ngOnInit() {
    this.initializeDate();
    this.initializeMap();
    this.resizeMap();
    this.getFloodWarnings();
  }


  public initializeDate(){
    this.dateControl.setValue(this.maxDate);
    if(this.dateControl.value){
      this.rangeDate = this.utilsApp.getDateRangeGeoglows(this.dateControl.value);
    }
  }

  public initializeMap() {
    // Base maps
    const osm = L.tileLayer(
      'https://abcd.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png', {
         zIndex: -1
      });
    const carto = L.tileLayer(
      'https://abcd.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
        zIndex: -1
      });
    const baseMaps = {
      "Light map": osm,
      'Dark map': carto
    };

    // Add base map
    this.map = L.map('map', { center: [30, 0], zoom: 2, zoomControl: false, });
    osm.addTo(this.map);

    // Add controls
    L.control.layers(baseMaps, {}, { position: 'topright' }).addTo(this.map);
    L.control.zoom({ position: 'topright' }).addTo(this.map);

    esri.dynamicMapLayer({
      url: 'https://livefeeds3.arcgis.com/arcgis/rest/services/GEOGLOWS/GlobalWaterModel_Medium/MapServer',
      opacity: 0.7
    }).addTo(this.map)

  }

  public resizeMap(): void {
    setTimeout(() => { this.map.invalidateSize() }, 10);
  }


  private getParamAlert(e: L.LeafletMouseEvent){
    // Conditions
    this.isReadyDataPlot = false;

    // Data
    const prop = e.layer.feature.properties;
    console.log(prop)

    this.basin = prop.basin;
    this.country = prop.country;
    this.hydroweb = prop.hydroweb;
    this.latitude = prop.latitude;
    this.longitude = prop.longitude;
    this.name = prop.name;
    this.reachid = prop.reachid;
    this.river = prop.river;
    this.state = prop.state;
    this.dateControlPanel.setValue(this.dateControl.value);
    this.template.showDataModal();

    setTimeout(() => {
      const elementWidth = this.panelPlot.nativeElement.offsetWidth;
      const urltemp = `${environment.urlAPI}/geoglows/plot-data?reachid=${this.reachid}&hydroweb=${this.hydroweb}&name=${this.name}&date=${this.rangeDate[0]}&width=${elementWidth}`;
      console.log(urltemp);
      fetch(urltemp)
      .then(response => response.text())
      .then(text => {
        const fixedText = text.replace(/NaN/g, 'null');
        return JSON.parse(fixedText);
      })
      .then((response) => {
        this.historicalSimulationPlot = response.hs;
        this.dailyAveragePlot = response.dp;
        this.monthlyAveragePlot = response.mp;
        this.forecastPlot = response.fp;
        this.metricTable = response.tb;
        this.isReadyDataPlot = true;
        fetch(`${environment.urlAPI}/geoglows/forecast-table?reachid=${this.reachid}&hydroweb=${this.hydroweb}&date=${this.rangeDate[0]}`)
          .then((response) => response.text())
          .then((response) => {
            this.renderer.setProperty(this.table.nativeElement, 'innerHTML', response);
          })
      })
    }, 300);
  }

  public getFloodWarnings(){
    const url = `${environment.urlAPI}/geoglows/water-level-alerts?date=${this.rangeDate[0]}`;
    console.log(url);
      fetch(url)
        .then((response) => response.json())
        .then((response)=> {
          this.geoglowsFloodWarningsDownload = response;
          this.geoglowsFloodWarnings = [
            this.utilsApp.filterByDayWaterLevel(response, "wd01"),
            this.utilsApp.filterByDayWaterLevel(response, "wd02"),
            this.utilsApp.filterByDayWaterLevel(response, "wd03"),
            this.utilsApp.filterByDayWaterLevel(response, "wd04"),
            this.utilsApp.filterByDayWaterLevel(response, "wd05"),
            this.utilsApp.filterByDayWaterLevel(response, "wd06"),
            this.utilsApp.filterByDayWaterLevel(response, "wd07"),
            this.utilsApp.filterByDayWaterLevel(response, "wd08"),
            this.utilsApp.filterByDayWaterLevel(response, "wd09"),
            this.utilsApp.filterByDayWaterLevel(response, "wd10"),
            this.utilsApp.filterByDayWaterLevel(response, "wd11"),
            this.utilsApp.filterByDayWaterLevel(response, "wd12"),
            this.utilsApp.filterByDayWaterLevel(response, "wd13"),
            this.utilsApp.filterByDayWaterLevel(response, "wd14"),
            this.utilsApp.filterByDayWaterLevel(response, "wd15")
          ];
          this.updateFloodWarnings();
        })
  }

  public floodIcon(data: any, rp: string) {
    const layers = this.utilsApp.filterByRP(data, rp);
    const customIcon = L.icon({
      iconUrl: `assets/icons/station/${rp}.png`,
      iconSize: [12, 16],
      iconAnchor: [8, 8]
    });
    return L.geoJSON(layers, {
      pointToLayer: (feature, latlng) =>
        L.marker(latlng, { icon: customIcon })
    });
  }


  public floodLayers: FloodLayers = {
    R2: null, R5: null, R10: null, R25: null, R50: null, R100: null,
  };

  public updateFloodWarnings(): void {
    const currentData = this.geoglowsFloodWarnings[this.activeDateIndex];
    this.geoglowsFlood000 && this.map.removeLayer(this.geoglowsFlood000);
    this.isActiveFlood000 && (this.geoglowsFlood000 = this.floodIcon(currentData, "R0").addTo(this.map));
    this.geoglowsFlood002 && this.map.removeLayer(this.geoglowsFlood002);
    this.isActiveFlood002 && (this.geoglowsFlood002 = this.floodIcon(currentData, "R2").addTo(this.map));
    this.geoglowsFlood005 && this.map.removeLayer(this.geoglowsFlood005);
    this.isActiveFlood005 && (this.geoglowsFlood005 = this.floodIcon(currentData, "R5").addTo(this.map));
    this.geoglowsFlood010 && this.map.removeLayer(this.geoglowsFlood010);
    this.isActiveFlood010 && (this.geoglowsFlood010 = this.floodIcon(currentData, "R10").addTo(this.map));
    this.geoglowsFlood025 && this.map.removeLayer(this.geoglowsFlood025);
    this.isActiveFlood025 && (this.geoglowsFlood025 = this.floodIcon(currentData, "R25").addTo(this.map));
    this.geoglowsFlood050 && this.map.removeLayer(this.geoglowsFlood050);
    this.isActiveFlood050 && (this.geoglowsFlood050 = this.floodIcon(currentData, "R50").addTo(this.map));
    this.geoglowsFlood100 && this.map.removeLayer(this.geoglowsFlood100);
    this.isActiveFlood100 && (this.geoglowsFlood100 = this.floodIcon(currentData, "R100").addTo(this.map));

    this.legendControl.onAdd = () => {
      const infoDiv = document.createElement('div');
      infoDiv.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
      infoDiv.style.color = 'black';
      infoDiv.style.padding = '5px';
      infoDiv.style.borderRadius = "5px"
      infoDiv.innerHTML = `<b>Flood Warnings</b><br>
                            <b>Initialized:</b> ${this.rangeDate[0]}<br>
                            <b>Forecast date:</b> ${this.rangeDate[this.activeDateIndex]}`;
      return(infoDiv)
    }
    this.legendControl.addTo(this.map);

    this.isActiveFlood000 && this.geoglowsFlood000.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood002 && this.geoglowsFlood002.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood005 && this.geoglowsFlood005.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood010 && this.geoglowsFlood010.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood025 && this.geoglowsFlood025.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood050 && this.geoglowsFlood050.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
    this.isActiveFlood100 && this.geoglowsFlood100.on("click", (e: L.LeafletMouseEvent) => this.getParamAlert(e))
  }


  public updateFloodWarningsDay(){
    if(this.dateControl.value){
      this.rangeDate = this.utilsApp.getDateRangeGeoglows(this.dateControl.value);
      this.activeDateIndex = 0;
      this.getFloodWarnings();
      this.dateControlPanel.setValue(this.dateControl.value);
    }
  }

  public nextTimeControl(){
    this.activeDateIndex++;
    if (this.activeDateIndex >= this.geoglowsFloodWarnings.length) {
      this.activeDateIndex = 0;
    }
    this.updateFloodWarnings();
  }

  public previuosTimeControl(){
    this.activeDateIndex--;
    if (this.activeDateIndex < 0) {
      this.activeDateIndex = this.geoglowsFloodWarnings.length - 1;
    }
    this.updateFloodWarnings();
  }

  public play(){
    if (this.intervalId == null) {
      this.intervalId = setInterval(() => {
          this.nextTimeControl()
      }, 400);
    }
  }

  public stop() {
    if (this.intervalId !== null) {
        clearInterval(this.intervalId);
        this.intervalId = null;
    }
  }

  public playTimeControl(){
    if (this.isPlay) {
      this.isPlay = false;
      this.stop();
    } else {
      this.isPlay = true;
      this.play();
    }
  }








  public captureMap(): void {
    const mapElement = document.getElementById('map');
    if (mapElement) {
      setTimeout(() => {
        html2canvas(mapElement, {
          useCORS: true,
          scale: window.devicePixelRatio
        }).then((canvas) => {
          const link = document.createElement('a');
          link.href = canvas.toDataURL('image/png');
          link.download = 'map.png';
          link.click();
        });
      }, 1000);
    }
  }



  public downloadSimulation(){
    const url = `${environment.urlAPI}/geoglows/corrected-simulation-csv?reachid=${this.reachid}&hydroweb=${this.hydroweb}`
    const link = document.createElement('a');
    link.href = url;
    link.click();

  }

  public downloadHydroweb(){
    const url = `${environment.urlAPI}/geoglows/observed-data-csv?hydroweb=${this.hydroweb}`
    const link = document.createElement('a');
    link.href = url;
    link.click();
  }

  public downloadForecast(){
    const url = `${environment.urlAPI}/geoglows/forecast-csv?reachid=${this.reachid}&hydroweb=${this.hydroweb}&date=${this.rangeDate[0]}`
    const link = document.createElement('a');
    link.href = url;
    link.click();

  }

  public downloadWarnings(){
    const jsonStr = JSON.stringify(this.geoglowsFloodWarningsDownload, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'warnings.json';
    a.click();
    window.URL.revokeObjectURL(url);
  }

}
