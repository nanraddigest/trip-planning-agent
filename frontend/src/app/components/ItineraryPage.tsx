import { useState, useEffect, useRef } from 'react';

const API_BASE = "http://localhost:8000";

interface ItineraryDay {
  day: number;
  activities: string[];
}

interface ItineraryPageProps {
  selectedPackage: any | null;
  searchData?: any;
}

export function ItineraryPage({ selectedPackage, searchData }: ItineraryPageProps) {
  const destination = selectedPackage?.destination
    || searchData?.destination
    || "";

  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([
    {
      role: 'assistant',
      content: destination
        ? `Hello! Ask me anything about your trip to ${destination} — I can suggest activities, food, neighborhoods, and tweak your itinerary.`
        : "Hello! I'm here to help you plan the perfect itinerary. What kind of activities are you interested in?"
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<ItineraryDay[]>([]);
  const [isLoadingItinerary, setIsLoadingItinerary] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
    async function init() {
      try {
        const res = await fetch(`${API_BASE}/api/trip/new`, { method: "POST" });
        const data = await res.json();
        setThreadId(data.thread_id);

        if (selectedPackage) {
          generateItinerary(data.thread_id);
        }
      } catch (e) {
        console.error("Failed to init conversation:", e);
      }
    }
    init();
  }, [selectedPackage]);

  async function generateItinerary(tid: string) {
    if (!selectedPackage) return;
    setIsLoadingItinerary(true);

    const destination = selectedPackage.destination
      || searchData?.destination
      || selectedPackage.flightInfo?.arrival
      || "the destination";

    const numDays = searchData?.startDate && searchData?.endDate
      ? Math.max(1, Math.ceil(
          (new Date(searchData.endDate).getTime() - new Date(searchData.startDate).getTime())
          / (1000 * 60 * 60 * 24)
        ))
      : 3;

    console.log("[itinerary] requesting", { destination, numDays, vibe: searchData?.chatMessage });

    try {
      const res = await fetch(`${API_BASE}/api/trip/itinerary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          destination,
          num_days: numDays,
          vibe: searchData?.chatMessage || "",
          thread_id: tid,
        }),
      });
      if (!res.ok) {
        const errText = await res.text();
        console.error("[itinerary] API error:", res.status, errText);
        return;
      }
      const data = await res.json();
      console.log("[itinerary] received", data);
      if (data.days && data.days.length > 0) {
        setItinerary(data.days);
      }
    } catch (e) {
      console.error("[itinerary] fetch failed:", e);
    } finally {
      setIsLoadingItinerary(false);
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !threadId) return;

    const userMsg = inputMessage;
    setChatMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInputMessage('');
    setIsSending(true);

    try {
      const res = await fetch(`${API_BASE}/api/trip/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          thread_id: threadId,
          destination,
        }),
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
      if (data.updated_itinerary) {
        setItinerary(data.updated_itinerary);
      }
    } catch (e) {
      setChatMessages(prev => [
        ...prev,
        { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {selectedPackage && (
        <div className="bg-gradient-to-r from-primary/10 to-transparent border-b border-border p-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <h2 className="text-foreground mb-2">Selected Package</h2>
              <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-foreground">{selectedPackage.flightInfo.airline}</span>
                  <span>•</span>
                  <span>{selectedPackage.flightInfo.departure} → {selectedPackage.flightInfo.arrival}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-foreground">{selectedPackage.hotelInfo.name}</span>
                  <span>•</span>
                  <span>{selectedPackage.hotelInfo.location}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl text-primary font-medium">${selectedPackage.totalPrice}</div>
              <p className="text-xs text-muted-foreground">per person</p>
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        <div className="max-w-7xl mx-auto h-full p-8 flex gap-6">
          <div className="w-1/4">
            <div className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col h-full">
              <div className="bg-gradient-to-r from-primary/10 to-transparent p-4 border-b border-border">
                <h3 className="text-foreground">Trip Assistant</h3>
                <p className="text-xs text-muted-foreground italic">Ask me anything about your trip</p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.map((message, idx) => (
                  <div
                    key={idx}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-xl p-3 ${
                        message.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-accent border border-border text-foreground'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                    </div>
                  </div>
                ))}
                {isSending && (
                  <div className="flex justify-start">
                    <div className="bg-accent border border-border rounded-xl p-3">
                      <p className="text-sm text-muted-foreground italic">Thinking...</p>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              <div className="p-4 border-t border-border">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Add museums, restaurants..."
                    disabled={isSending}
                    className="flex-1 px-3 py-2 bg-background rounded-lg border border-border focus:border-primary focus:outline-none transition-colors text-sm disabled:opacity-50"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={isSending}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-foreground mb-1">Your Itinerary</h2>
                <p className="text-sm text-muted-foreground italic">A curated journey crafted for you</p>
              </div>
              <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm">
                Export Itinerary
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {isLoadingItinerary ? (
                <div className="flex items-center justify-center py-16">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto mb-3"></div>
                    <p className="text-muted-foreground italic text-sm">
                      Generating your itinerary...
                    </p>
                  </div>
                </div>
              ) : itinerary.length === 0 ? (
                <div className="flex items-center justify-center py-16">
                  <p className="text-muted-foreground italic text-sm">
                    Select a package to generate your itinerary.
                  </p>
                </div>
              ) : (
                itinerary.map((day) => (
                  <div key={day.day} className="bg-card border border-border rounded-xl overflow-hidden">
                    <div className="bg-gradient-to-r from-primary/10 to-transparent p-3 border-b border-border">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary/20 rounded-full flex items-center justify-center">
                          <span className="text-primary font-medium text-sm">{day.day}</span>
                        </div>
                        <h3 className="text-foreground text-sm">Day {day.day}</h3>
                      </div>
                    </div>

                    <div className="p-3 space-y-2">
                      {day.activities.map((activity, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-2 bg-accent/20 rounded-lg border border-border hover:bg-accent/40 transition-colors"
                        >
                          <div className="w-1.5 h-1.5 bg-primary rounded-full flex-shrink-0"></div>
                          <p className="text-sm text-foreground flex-1">{activity}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
