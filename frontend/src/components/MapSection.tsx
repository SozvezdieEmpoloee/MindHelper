import { useEffect, useMemo, useRef, useState } from "react";
import {
  ApiError,
  getEmergencyResources,
  getSpecialists,
  type EmergencyResource,
  type Specialist,
  type SpecialistLocation,
} from "../utils/api";

const YANDEX_MAPS_API_KEY =
  import.meta.env.VITE_YANDEX_MAPS_API_KEY ?? "eb2ada3f-413e-4a53-96cc-2c4bc7c57a22";
const VORONEZH_CENTER = [51.6608, 39.2003];

declare global {
  interface Window {
    ymaps: {
      ready: (callback: () => void) => void;
      Map: new (container: HTMLElement, options: unknown) => YandexMap;
      Placemark: new (
        coordinates: number[],
        properties: Record<string, unknown>,
        options: Record<string, unknown>,
      ) => unknown;
    };
  }
}

interface YandexMap {
  destroy: () => void;
  setZoom: (zoom: number) => void;
  setBounds: (bounds: unknown, options?: Record<string, unknown>) => void;
  panTo: (coordinates: number[], options?: Record<string, unknown>) => Promise<void>;
  geoObjects: {
    add: (item: unknown) => void;
    getLength: () => number;
    getBounds: () => unknown;
  };
}

function loadYandexMapsScript(apiKey: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.ymaps) {
      resolve();
      return;
    }

    const script = document.createElement("script");
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`;
    script.type = "text/javascript";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Не удалось загрузить Яндекс Карты."));
    document.head.appendChild(script);
  });
}

function formatPrice(location: SpecialistLocation) {
  if (!location.consultation_price) {
    return "Уточняйте по телефону";
  }
  return `${Intl.NumberFormat("ru-RU").format(Number(location.consultation_price))} ${location.currency}`;
}

function professionLabel(value: Specialist["profession"]) {
  return value === "psychiatrist" ? "Психиатр" : "Психолог";
}

export function MapSection() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<YandexMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [directoryError, setDirectoryError] = useState<string | null>(null);
  const [specialists, setSpecialists] = useState<Specialist[]>([]);
  const [resources, setResources] = useState<EmergencyResource[]>([]);

  const locations = useMemo(
    () =>
      specialists.flatMap((specialist) =>
        specialist.locations.map((location) => ({
          specialist,
          location: {
            ...location,
            latitude: Number(location.latitude),
            longitude: Number(location.longitude),
            consultation_price:
              location.consultation_price === null ? null : Number(location.consultation_price),
          },
        })),
      ),
    [specialists],
  );

  useEffect(() => {
    let cancelled = false;

    const loadDirectory = async () => {
      try {
        const [specialistResponse, resourceResponse] = await Promise.all([
          getSpecialists(),
          getEmergencyResources(),
        ]);
        if (cancelled) {
          return;
        }
        setSpecialists(specialistResponse);
        setResources(resourceResponse);
      } catch (error) {
        if (cancelled) {
          return;
        }
        setDirectoryError(
          error instanceof ApiError
            ? error.message
            : "Не удалось загрузить контакты помощи и список специалистов.",
        );
      }
    };

    void loadDirectory();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!locations.length) {
      return;
    }

    let isMounted = true;

    const initMap = async () => {
      try {
        await loadYandexMapsScript(YANDEX_MAPS_API_KEY);
        if (!isMounted || !mapContainerRef.current) {
          return;
        }

        window.ymaps.ready(() => {
          if (!isMounted || !mapContainerRef.current) {
            return;
          }

          mapRef.current = new window.ymaps.Map(mapContainerRef.current, {
            center: VORONEZH_CENTER,
            zoom: 12,
            controls: ["zoomControl", "searchControl", "geolocationControl"],
          });

          locations.forEach(({ specialist, location }) => {
            const placemark = new window.ymaps.Placemark(
              [location.latitude, location.longitude],
              {
                balloonContent: `
                  <div style="padding: 10px; max-width: 320px;">
                    <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${specialist.full_name}</h3>
                    <p style="margin: 0 0 6px 0; font-size: 14px; color: #475569;">${professionLabel(specialist.profession)}</p>
                    <p style="margin: 0 0 6px 0; font-size: 14px; color: #475569;">${location.address_line}</p>
                    <p style="margin: 0; font-size: 14px; color: #475569;">${formatPrice(location)}</p>
                  </div>
                `,
              },
              {
                preset: specialist.profession === "psychiatrist" ? "islands#redIcon" : "islands#blueIcon",
              },
            );
            mapRef.current?.geoObjects.add(placemark);
          });

          if (mapRef.current && mapRef.current.geoObjects.getLength() > 0) {
            mapRef.current.setBounds(mapRef.current.geoObjects.getBounds(), {
              checkZoomRange: true,
            });
          }

          setMapLoaded(true);
        });
      } catch (error) {
        console.error(error);
        if (isMounted) {
          setMapError("Не удалось загрузить карту. Список специалистов остаётся доступным ниже.");
        }
      }
    };

    void initMap();

    return () => {
      isMounted = false;
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
      }
    };
  }, [locations]);

  const flyToLocation = (location: SpecialistLocation) => {
    if (!mapRef.current) {
      return;
    }
    void mapRef.current
      .panTo([location.latitude, location.longitude], { flying: true, duration: 800 })
      .then(() => mapRef.current?.setZoom(16));
  };

  return (
    <section className="bg-white py-20" id="clinics">
      <div className="mx-auto max-w-6xl px-6">
        <div className="text-center">
          <span className="inline-block rounded-full bg-sky-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">
            Помощь рядом
          </span>
          <h2 className="mt-4 text-3xl font-black text-slate-950 md:text-4xl">
            Экстренные контакты и специалисты в Воронеже
          </h2>
          <p className="mx-auto mt-4 max-w-3xl text-base leading-relaxed text-slate-600">
            Здесь собраны контакты горячих линий и очных специалистов, к которым можно обратиться,
            если нужна срочная или плановая поддержка.
          </p>
        </div>

        {directoryError && (
          <div className="mt-8 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
            {directoryError}
          </div>
        )}

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {resources.map((resource) => (
            <article
              key={resource.id}
              className="rounded-[28px] border border-slate-200 bg-slate-50 p-6 shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-rose-600">
                Экстренная помощь
              </p>
              <h3 className="mt-3 text-xl font-bold text-slate-900">{resource.service_name}</h3>
              <p className="mt-3 text-lg font-semibold text-slate-900">{resource.contact_phone}</p>
              {resource.contact_url && (
                <a
                  href={resource.contact_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 inline-block text-sm font-semibold text-sky-700 transition hover:text-sky-600"
                >
                  Открыть сайт
                </a>
              )}
            </article>
          ))}
        </div>

        <div className="relative mt-10 overflow-hidden rounded-[32px] border border-slate-200 shadow-xl">
          <div ref={mapContainerRef} className="h-80 w-full md:h-[28rem]" />

          {!mapLoaded && !mapError && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50/90">
              <div className="inline-flex items-center gap-3 rounded-2xl bg-white px-6 py-4 text-sm font-medium text-slate-700 shadow">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-sky-200 border-t-sky-500" />
                Загружаем карту специалистов...
              </div>
            </div>
          )}

          {mapError && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50/95 p-6">
              <div className="max-w-md rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-lg">
                <h3 className="text-lg font-bold text-slate-900">Карта временно недоступна</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">{mapError}</p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {locations.map(({ specialist, location }) => (
            <article
              key={location.id}
              className="rounded-[26px] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
            >
              <span
                className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${
                  specialist.profession === "psychiatrist"
                    ? "bg-rose-100 text-rose-700"
                    : "bg-sky-100 text-sky-700"
                }`}
              >
                {professionLabel(specialist.profession)}
              </span>
              <h3 className="mt-4 text-base font-bold leading-snug text-slate-900">
                {specialist.full_name}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">{location.address_line}</p>
              <p className="mt-2 text-sm font-medium text-slate-800">{formatPrice(location)}</p>
              <button
                type="button"
                onClick={() => flyToLocation(location)}
                className="mt-4 w-full rounded-2xl bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-sky-50 hover:text-sky-700"
              >
                Показать на карте
              </button>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
