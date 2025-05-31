
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";

export const PropertySearch = () => {
  const [postcode, setPostcode] = useState("");
  const [propertyType, setPropertyType] = useState("For Sale");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!postcode.trim()) {
      toast.error("Please enter a postcode");
      return;
    }

    setIsSearching(true);
    console.log(`Searching for ${propertyType} properties in ${postcode}`);
    
    try {
      // This is where the web scraping logic would go
      // For now, we'll simulate the search
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast.success(`Found properties in ${postcode}! (This is a demo - real scraping would happen here)`);
      
      // Here you would scrape based on propertyType:
      // - "For Sale" would scrape Rightmove, Zoopla sale listings
      // - "For Rent" would scrape rental listings
      console.log(`Would scrape ${propertyType} from Zoopla and Rightmove for postcode: ${postcode}`);
      
    } catch (error) {
      toast.error("Error searching for properties");
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-sm animate-fadeIn">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Postcode</label>
          <Input 
            type="text" 
            placeholder="Enter postcode (e.g. SW1A 1AA)"
            value={postcode}
            onChange={(e) => setPostcode(e.target.value)}
            className="w-full"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Property Type</label>
          <select 
            className="w-full p-2 border rounded-md"
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
          >
            <option>For Sale</option>
            <option>For Rent</option>
          </select>
        </div>
      </div>
      <Button 
        className="w-full bg-gray-900 text-white hover:bg-gray-800 transition-colors"
        onClick={handleSearch}
        disabled={isSearching}
      >
        {isSearching ? "Searching Properties..." : "Search Properties"}
      </Button>
    </div>
  );
};
