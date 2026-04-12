import { useEffect, useRef, useState } from "react";

// ВАШ API-КЛЮЧ ЯНДЕКС.КАРТ
// Получите его здесь: https://developer.tech.yandex.ru/
const YANDEX_MAPS_API_KEY = "eb2ada3f-413e-4a53-96cc-2c4bc7c57a22"; // <-- ВСТАВЬТЕ СВОЙ КЛЮЧ

// Центр Воронежа
const VORONEZH_CENTER = [51.6608, 39.2003];

const clinics = [
  {
    id: 1,
    name: "Городская клиническая психиатрическая больница №2",
    address: "ул. Орджоникидзе, 89, Воронеж",
    phone: "+7 (473) 252-01-14",
    hours: "Пн–Пт: 8:00–17:00",
    type: "Государственное учреждение",
    color: "bg-blue-100 text-blue-700",
    coordinates: [51.6785, 39.2135],
  },
  {
    id: 2,
    name: "Центр психологической помощи «Гармония»",
    address: "пр-т Революции, 29, Воронеж",
    phone: "+7 (473) 255-44-33",
    hours: "Пн–Сб: 9:00–21:00",
    type: "Частная клиника",
    color: "bg-purple-100 text-purple-700",
    coordinates: [51.6721, 39.2154],
  },
  {
    id: 3,
    name: "Психоневрологический диспансер №3",
    address: "ул. Ленинградская, 64, Воронеж",
    phone: "+7 (473) 255-89-10",
    hours: "Пн–Пт: 8:00–20:00",
    type: "Государственное учреждение",
    color: "bg-emerald-100 text-emerald-700",
    coordinates: [51.6568, 39.2256],
  },
  {
    id: 4,
    name: "Центр семейной психологии",
    address: "ул. 20-летия Октября, 119, Воронеж",
    phone: "+7 (473) 223-65-41",
    hours: "Пн–Пт: 10:00–19:00",
    type: "Частная клиника",
    color: "bg-rose-100 text-rose-700",
    coordinates: [51.6789, 39.1847],
  },
];

// Тип для Яндекс.Карт
declare global {
  interface Window {
    ymaps: any;
  }
}

// Загрузка скрипта Яндекс.Карт
const loadYandexMapsScript = (apiKey: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.ymaps) {
      resolve();
      return;
    }

    const script = document.createElement("script");
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU`;
    script.type = "text/javascript";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Не удалось загрузить Яндекс.Карты"));
    document.head.appendChild(script);
  });
};

export function MapSection() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Функция перемещения карты к выбранной клинике
  const flyToClinic = (coordinates: number[]) => {
    if (mapRef.current && coordinates) {
      mapRef.current.panTo(coordinates, {
        flying: true,
        duration: 1000,
      }).then(() => {
        mapRef.current.setZoom(16);
      });
    }
  };

  useEffect(() => {
    // Проверка, что API-ключ вставлен
    if (YANDEX_MAPS_API_KEY === "ВАШ_API_КЛЮЧ_ЗДЕСЬ" || !YANDEX_MAPS_API_KEY) {
      setMapError("API-ключ Яндекс.Карт не вставлен. Отредактируйте файл src/components/MapSection.tsx");
      return;
    }

    let isMounted = true;

    const initMap = async () => {
      try {
        // Загружаем скрипт Яндекс.Карт
        await loadYandexMapsScript(YANDEX_MAPS_API_KEY);

        if (!isMounted || !mapContainerRef.current) return;

        // Инициализируем карту
        window.ymaps.ready(() => {
          if (!isMounted || !mapContainerRef.current) return;

          // Создаем карту (центр - Воронеж)
          mapRef.current = new window.ymaps.Map(mapContainerRef.current, {
            center: VORONEZH_CENTER,
            zoom: 12,
            controls: ["zoomControl", "searchControl", "geolocationControl"],
          });

          // Добавляем метки клиник
          clinics.forEach((clinic) => {
            if (!clinic.coordinates) return; // Пропускаем клиники без координат

            const placemark = new window.ymaps.Placemark(
              clinic.coordinates,
              {
                balloonContent: `
                  <div style="padding: 10px; max-width: 300px;">
                    <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: bold;">${clinic.name}</h3>
                    <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">${clinic.address}</p>
                    <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">📞 ${clinic.phone}</p>
                    <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">🕐 ${clinic.hours}</p>
                    <p style="margin: 0; font-size: 12px; color: #999;">${clinic.type}</p>
                  </div>
                `,
              },
              {
                preset: "islands#blueIcon",
                iconColor: clinic.color.includes("blue") 
                  ? "#3b82f6" 
                  : clinic.color.includes("purple") 
                  ? "#8b5cf6" 
                  : clinic.color.includes("emerald") 
                  ? "#10b981" 
                  : "#ef4444",
              }
            );

            mapRef.current.geoObjects.add(placemark);
          });

          // Центрируем карту на всех метках
          if (mapRef.current.geoObjects.getLength() > 0) {
            mapRef.current.setBounds(mapRef.current.geoObjects.getBounds(), {
              checkZoomRange: true,
            });
          }

          setMapLoaded(true);
        });
      } catch (error) {
        console.error("Ошибка загрузки Яндекс.Карт:", error);
        setMapError("Не удалось загрузить карту. Проверьте API-ключ и подключение к интернету.");
      }
    };

    initMap();

    return () => {
      isMounted = false;
      if (mapRef.current) {
        mapRef.current.destroy();
      }
    };
  }, []);

  return (
    <section className="py-20 bg-white" id="clinics">
      <div className="mx-auto max-w-6xl px-6">
        <div className="text-center mb-12">
          <span className="inline-block rounded-full bg-blue-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-blue-600 mb-4">
            Найти помощь рядом
          </span>
          <h2 className="text-3xl font-bold text-slate-800 md:text-4xl">
            Психологическая помощь в Воронеже
          </h2>
          <p className="mt-3 text-slate-500 max-w-xl mx-auto">
            Адреса клиник Воронежа загружаются из базы данных Django и отображаются на интерактивной карте.
          </p>
        </div>

        {/* Яндекс.Карта */}
        <div className="relative rounded-3xl overflow-hidden border border-slate-200 shadow-xl mb-10">
          {/* Контейнер для карты */}
          <div ref={mapContainerRef} className="h-80 md:h-96 w-full" />

          {/* Сообщение об ошибке, если API-ключ не вставлен */}
          {mapError && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50">
              <div className="text-center p-8 bg-white rounded-2xl shadow-lg border border-slate-200 max-w-md mx-4">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="font-bold text-slate-800 mb-2">Карта не подключена</h3>
                <p className="text-sm text-slate-500 mb-4">
                  {mapError}
                </p>
                <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-600 text-left">
                  <p className="mb-1"><strong>Шаг 1:</strong> Получите API-ключ на https://developer.tech.yandex.ru/</p>
                  <p><strong>Шаг 2:</strong> Откройте файл src/components/MapSection.tsx</p>
                  <p><strong>Шаг 3:</strong> Замените "ВАШ_API_КЛЮЧ_ЗДЕСЬ" на ваш ключ</p>
                </div>
              </div>
            </div>
          )}

          {/* Индикатор загрузки */}
          {!mapLoaded && !mapError && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-50">
              <div className="text-center">
                <div className="inline-flex items-center gap-3 rounded-2xl bg-white px-6 py-4 shadow-lg border border-slate-200">
                  <div className="h-5 w-5 rounded-full border-2 border-blue-200 border-t-blue-500 animate-spin" />
                  <span className="text-sm font-medium text-slate-700">Загрузка карты...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Clinic Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {clinics.map((clinic) => (
            <div
              key={clinic.id}
              className="group rounded-2xl border border-slate-100 bg-white p-5 shadow-sm transition hover:shadow-md hover:-translate-y-1"
            >
              <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold mb-3 ${clinic.color}`}>
                {clinic.type}
              </span>
              <h3 className="font-semibold text-slate-800 text-sm leading-snug mb-2">
                {clinic.name}
              </h3>
              <div className="space-y-1.5 text-xs text-slate-500">
                <div className="flex items-start gap-1.5">
                  <svg className="h-3.5 w-3.5 mt-0.5 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                  </svg>
                  {clinic.address}
                </div>
                <div className="flex items-center gap-1.5">
                  <svg className="h-3.5 w-3.5 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>
                  </svg>
                  {clinic.phone}
                </div>
                <div className="flex items-center gap-1.5">
                  <svg className="h-3.5 w-3.5 shrink-0 text-slate-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/>
                  </svg>
                  {clinic.hours}
                </div>
              </div>
              <button 
                onClick={() => flyToClinic(clinic.coordinates)}
                disabled={!clinic.coordinates}
                className={`mt-4 w-full rounded-xl py-2 text-xs font-semibold transition ${
                  clinic.coordinates 
                    ? "bg-slate-50 text-slate-600 hover:bg-blue-50 hover:text-blue-600" 
                    : "bg-gray-100 text-gray-400 cursor-not-allowed"
                }`}
              >
                {clinic.coordinates ? "На карте →" : "Нет адреса"}
              </button>
            </div>
          ))}
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          * Карта отображает психологические центры в Воронеже. Адреса загружаются из базы данных Django.
        </p>
      </div>
    </section>
  );
}
